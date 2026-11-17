(()=>{"use strict";function init(){const root=document.getElementById("living-archive-navigator");if(!root||root.dataset.lanInitialized==="true")return;root.dataset.lanInitialized="true";const C=Object.assign({endpoint:"",timeoutMs:50000},window.LIVING_ARCHIVE_NAVIGATOR_CONFIG||{}),state={choice:"",situation:"",possibility:"",clarification:""},panels=[...root.querySelectorAll("[data-state]")],show=n=>{panels.forEach(p=>p.hidden=p.dataset.state!==n);root.scrollIntoView({behavior:"smooth",block:"start"})},clean=v=>String(v||"").replace(/\s+/g," ").trim(),displayTitle=v=>String(v||"").replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F1E6}-\u{1F1FF}\uFE0F\u200D]/gu,"").replace(/\s{2,}/g," ").trim(),esc=v=>String(v||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]||c));function consumeNativeQuery(){const params=new URLSearchParams(window.location.search),q=clean(params.get("navigator_query")||"");if(!q)return false;state.choice="understanding";state.situation=q;const input=document.getElementById("lan-situation");if(input)input.value=q;params.delete("navigator_query");const next=params.toString(),url=window.location.pathname+(next?"?"+next:"")+window.location.hash;window.history.replaceState({},document.title,url);show("situation");if(input)input.focus();return true}function render(r){
const a=document.getElementById("lan-reflection"),d=document.getElementById("lan-doors");
if(!a||!d)return;
a.replaceChildren();
if(typeof r.reflection==="string"){
r.reflection.split(/\n\s*\n/).filter(Boolean).forEach(function(part){
const p=document.createElement("p");p.className="sp-opening";p.textContent=part.trim();a.appendChild(p);
});
}
d.replaceChildren();
const helper=window.LivingArchiveAnswerDoorway;
const items=(Array.isArray(r.selected)?r.selected:[]).map(function(x){
return {title:displayTitle(x&&x.title),url:x&&x.url,rationale:clean(r.why_each&&r.why_each[x.id]||""),kind:"continue"};
});
if(!helper||typeof helper.renderMany!=="function")return;
const count=helper.renderMany(d,items);
if(count!==3){d.replaceChildren();return;}
const landscape=Array.isArray(r.landscape)?r.landscape:[];
const safe=[];
landscape.forEach(function(x){
if(!x||typeof x.title!=="string")return;
const url=helper.normalizeUrl&&helper.normalizeUrl(x.url),title=displayTitle(x.title);
if(url&&title)safe.push({url:url,title:title});
});
if(safe.length){
const section=document.createElement("section");section.className="sp-landscape";
const heading=document.createElement("h3");heading.textContent="Continue exploring the Archive";
const copy=document.createElement("p");copy.textContent="If you want to keep going after these, the wider Archive offers other ways into the question.";
const nav=document.createElement("nav");nav.className="sp-landscape-links";nav.setAttribute("aria-label","Continue exploring the Archive");
safe.forEach(function(x){const link=document.createElement("a");link.href=x.url;link.textContent=x.title;nav.appendChild(link);});
section.append(heading,copy,nav);d.appendChild(section);
}
}
function showClarification(r){const q=document.getElementById("lan-clarifying-question"),i=document.getElementById("lan-clarification");if(q)q.textContent=clean(r.clarifying_question)||"What part of this question feels most important to understand?";if(i)i.value="";show("clarification");if(i)i.focus()}async function request(){if(!C.endpoint)throw Error("The navigator service has not been connected yet.");const ac=new AbortController(),t=setTimeout(()=>ac.abort(),C.timeoutMs);try{const r=await fetch(C.endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({version:"0.3.1",choice:state.choice,situation:state.situation,possibility:state.possibility,clarification:state.clarification}),signal:ac.signal});if(!r.ok)throw Error(`Navigator service returned ${r.status}.`);const x=await r.json();if(x.needs_clarification&&!state.clarification){return x}if(!Array.isArray(x.selected)||x.selected.length<3)throw Error("Fewer than three canonical destinations were returned.");return x}finally{clearTimeout(t)}}function fail(e){const a=document.getElementById("lan-reflection"),d=document.getElementById("lan-doors");if(a){a.replaceChildren();const p=document.createElement("p");p.textContent="Something interrupted the path before it could open. Please try again.";a.appendChild(p);}if(d)d.replaceChildren();console.error("Living Archive Navigator:",e);show("result")}async function openPath(){show("listening");try{const result=await request();if(result.needs_clarification&&!state.clarification){showClarification(result);return}render(result);show("result")}catch(e){fail(e)}}root.addEventListener("click",async e=>{const action=e.target.closest("[data-action]")?.dataset.action,opt=e.target.closest("[data-choice]");if(opt){state.choice=opt.dataset.choice||"";show("situation");return}if(action==="begin"){show("orientation");return}if(action==="continue-situation"){state.situation=clean(document.getElementById("lan-situation")?.value);if(state.situation)show("possibility");return}if(action==="listen"){state.possibility=clean(document.getElementById("lan-possibility")?.value);state.clarification="";if(state.possibility)await openPath();return}if(action==="submit-clarification"){state.clarification=clean(document.getElementById("lan-clarification")?.value);if(state.clarification)await openPath();return}if(action==="restart"){state.choice=state.situation=state.possibility=state.clarification="";document.getElementById("lan-situation").value="";document.getElementById("lan-possibility").value="";document.getElementById("lan-clarification").value="";show("intro")}});if(!consumeNativeQuery())show("intro")}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init()})();

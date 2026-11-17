(()=>{"use strict";function init(){const root=document.getElementById("stewardship-pathway");if(!root||root.dataset.spInitialized==="true")return;root.dataset.spInitialized="true";const C=Object.assign({endpoint:"",timeoutMs:30000},window.STEWARDSHIP_PATHWAY_CONFIG||{}),state={choice:"",situation:"",possibility:""},panels=[...root.querySelectorAll("[data-state]")],show=n=>{panels.forEach(p=>p.hidden=p.dataset.state!==n);root.scrollIntoView({behavior:"smooth",block:"start"})},clean=v=>String(v||"").replace(/\s+/g," ").trim(),displayTitle=v=>String(v||"").replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F1E6}-\u{1F1FF}\uFE0F\u200D]/gu,"").replace(/\s{2,}/g," ").trim(),esc=v=>String(v||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));function render(r){
const a=document.getElementById("sp-reflection"),d=document.getElementById("sp-doors");
if(!a||!d)throw Error("Pathway result containers are unavailable.");
a.replaceChildren();
if(typeof r.reflection==="string"&&r.reflection.trim()){
const p=document.createElement("p");p.className="sp-opening";p.textContent=r.reflection.trim();a.appendChild(p);
}
d.replaceChildren();
const helper=window.LivingArchiveAnswerDoorway;
const selected=Array.isArray(r.selected)?r.selected:[];
const items=selected.map(x=>({
title:displayTitle(x&&x.title),
url:x&&x.url,
rationale:clean(r.why_each&&((r.why_each[x.id])||(r.why_each[x.title]))||""),
kind:"continue"
}));
if(!helper||typeof helper.renderMany!=="function"||helper.renderMany(d,items)!==3){
throw Error("The pathway did not return three complete, verified destinations.");
}
const landscape=Array.isArray(r.landscape)?r.landscape:[];
const safeLandscape=[];
landscape.forEach(x=>{
if(!x||typeof x.title!=="string"||!helper.normalizeUrl)return;
const url=helper.normalizeUrl(x.url);
const title=displayTitle(x.title);
if(url&&title)safeLandscape.push({title:title,url:url});
});
if(safeLandscape.length){
const section=document.createElement("section");section.className="sp-landscape";
const heading=document.createElement("h3");heading.textContent="Explore the wider Stewardship landscape";
const copy=document.createElement("p");copy.textContent="These are only a few of the places available to you beyond this particular path.";
const nav=document.createElement("nav");nav.className="sp-landscape-links";nav.setAttribute("aria-label","Explore the wider Stewardship landscape");
safeLandscape.forEach(item=>{
const link=document.createElement("a");link.href=item.url;link.textContent=item.title;nav.appendChild(link);
});
section.append(heading,copy,nav);d.appendChild(section);
}
}
async function request(){if(!C.endpoint)throw Error("The pathway service has not been connected yet.");const ac=new AbortController(),t=setTimeout(()=>ac.abort(),C.timeoutMs);try{const r=await fetch(C.endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({version:"3.4.3",choice:state.choice,situation:state.situation,possibility:state.possibility}),signal:ac.signal});if(!r.ok)throw Error(`Pathway service returned ${r.status}.`);const x=await r.json();if(!Array.isArray(x.selected)||x.selected.length!==3)throw Error("The pathway did not return three canonical destinations.");return x}finally{clearTimeout(t)}}function fail(e){const a=document.getElementById("sp-reflection"),d=document.getElementById("sp-doors");if(a){a.replaceChildren();const p=document.createElement("p");p.textContent="Something interrupted the path before it could open. Please try again.";a.appendChild(p);}if(d)d.replaceChildren();console.error("Stewardship Pathway:",e);show("result")}root.addEventListener("click",async e=>{const action=e.target.closest("[data-action]")?.dataset.action,opt=e.target.closest("[data-choice]");if(opt){state.choice=opt.dataset.choice||"";show("situation");return}if(action==="begin"){show("orientation");return}if(action==="continue-situation"){state.situation=clean(document.getElementById("sp-situation")?.value);if(state.situation)show("possibility");return}if(action==="listen"){state.possibility=clean(document.getElementById("sp-possibility")?.value);show("listening");try{render(await request());show("result")}catch(e){fail(e)}return}if(action==="restart"){state.choice=state.situation=state.possibility="";document.getElementById("sp-situation").value="";document.getElementById("sp-possibility").value="";show("intro")}});show("intro")}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init()})();

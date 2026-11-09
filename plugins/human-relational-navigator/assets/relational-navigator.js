(function(){
'use strict';
/* HRN v0.5.165 — adapter-owned Guide return + closure question continuity */
function ready(fn){document.readyState!=='loading'?fn():document.addEventListener('DOMContentLoaded',fn)}
ready(function(){
 document.querySelectorAll('.lah-rn').forEach(function(root){
  if(root.dataset.lahRnInitialized==='1')return;
  root.dataset.lahRnInitialized='1';
  var form=root.querySelector('.lah-rn-form'),input=root.querySelector('.lah-rn-input'),current=root.querySelector('.lah-rn-current'),actions=root.querySelector('.lah-rn-unit-actions'),submit=root.querySelector('.lah-rn-submit'),handoffStatus=root.querySelector('.lah-rn-handoff-status');
  var recordTools=root.querySelector('.lah-rn-record-tools'),viewRecord=root.querySelector('.lah-rn-view-record'),printButton=root.querySelector('.lah-rn-print'),record=root.querySelector('.lah-rn-record'),recordBody=root.querySelector('.lah-rn-record-body'),recordClose=root.querySelector('.lah-rn-record-close');
  if(!form||!input||!current||!actions||!submit||!recordTools||!record||typeof LAHRN==='undefined')return;

  var turns=[],loading=false,recordAvailable=false,unitTurns=0;
  var pendingVisitorMessage=null;
  var safetyStage='green',safetyQuestion='',safetyMessage='',country='';
  var threadSummary='',workingHypothesis='',unresolved='',underlyingNeed='',desiredCondition='',emergingDelta='',perspectiveDelta='',bodyOfThought='',movementDirection='',nextMovement='',resourceFit='';
  var fractalStage='opening',fractalTransition='',newTerrain='',completedInsight='',nextHorizon='',conversationPurpose='',currentFractal='',fractalMaturity='',pivotSignal='',leadershipNeed='';
  var fractalHistory=[];
  var journeySynthesis='',junctionSummary='',segmentOpening='',segmentIndex=1,finalizing=false;
  var junctionNudges=[
   'We have reached a thoughtful point. Would you like to continue from here?',
   'Something has come together in this exchange. Would you like to keep going?',
   'We seem to have arrived at a useful point of understanding. Continue?',
   'This feels like a natural place to pause. Would you like to explore further?',
   'A meaningful thread has emerged here. Would you like to follow it onward?',
   'We have uncovered something worth noticing. Would you like to continue?',
   'There is a new perspective here. Would you like to see where it leads?',
   'This exchange has opened a different way of seeing things. Continue from here?',
   'Something seems clearer now. Would you like to keep exploring?',
   'We have come to a natural point in the conversation. Would you like to go on?',
   'A useful distinction has emerged. Would you like to carry it further?',
   'We have reached a point where the conversation could open somewhere new. Continue?'
  ];
  function nextJunctionNudge(){return junctionNudges[Math.max(0,(segmentIndex-1)%junctionNudges.length)];}
  function ordinaryInputPlaceholder(){return 'Share what comes to mind.';}
  function clearGuideHandoffState(){
   if(pendingHandoffVisitor){pendingHandoffVisitor.remove();pendingHandoffVisitor=null;}
   guideSeed='';
   root.classList.remove('is-guide-handoff');
   if(handoffStatus)handoffStatus.hidden=true;
   input.value='';
   input.removeAttribute('aria-busy');
   input.placeholder=ordinaryInputPlaceholder();
  }
  function responseLooksLikeEnvelope(value){
   var raw=String(value||'').trim();
   return raw.charAt(0)==='{' && (/^\\s*\\{\\s*[\"']?response[\"']?\\s*:/i.test(raw)||/[\"']response[\"']?\\s*:\\s*[\"']/i.test(raw));
  }
  function normalizeResponseEnvelope(data){
   if(!data||typeof data.response!=='string')return data;
   var raw=data.response.trim();
   if(raw.charAt(0)!=='{')return data;
   try{
    var nested=JSON.parse(raw);
    if(nested&&typeof nested==='object'&&typeof nested.response==='string'){
     var merged={};Object.keys(data).forEach(function(k){merged[k]=data[k]});Object.keys(nested).forEach(function(k){merged[k]=nested[k]});return merged;
    }
   }catch(e){}
   return data;
  }
  var safetyIdleTimer=null,safetyRevealTimer=null;
  var guideSession='';
  var originalQuestion='';
  var pendingHandoffVisitor=null;
  var guideReturnPending=false,guideReturnComplete=false;
  var journeySession='';
  var urlParams=new URLSearchParams(window.location.search);
  // Accept the canonical Guide handoff name plus legacy/browser seed names.
  // The explicit question is carried into REST as original_question.
  var guideSeed=(urlParams.get('hrn_question')||urlParams.get('guide_question')||urlParams.get('original_question')||urlParams.get('question')||urlParams.get('query')||urlParams.get('hrn_seed')||'').trim();
  guideSession=(urlParams.get('hrn_session')||'').trim();
  journeySession=guideSession||((function(){try{var existing=sessionStorage.getItem('lah_hrn_journey_session');if(existing)return existing;var created='hrn-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10);sessionStorage.setItem('lah_hrn_journey_session',created);return created}catch(e){return 'hrn-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10)}})());

  function escapeText(value){return String(value||'').replace(/\r\n/g,'\n').trim()}
  function renderText(container,text,kind){
   var normalized=escapeText(text);
   var paragraphs=normalized.split(/\n\s*\n+/).map(function(part){return part.trim()}).filter(Boolean);
   paragraphs.forEach(function(part){var p=document.createElement('p');p.textContent=part;container.appendChild(p)});
   if(!paragraphs.length&&normalized)container.textContent=normalized;
   if(kind)container.classList.add('lah-rn-copy--'+kind);
  }
  function appendCurrent(visitorText,responseText,question,resource,intro,accessIntro){
   var visitor=document.createElement('div');visitor.className='lah-rn-message lah-rn-message--visitor';renderText(visitor,visitorText,'visitor');current.appendChild(visitor);
   var navigator=document.createElement('div');navigator.className='lah-rn-message lah-rn-message--navigator';renderText(navigator,responseText,'navigator');
   if(question){var q=document.createElement('p');q.className='lah-rn-question';q.textContent=String(question).trim();navigator.appendChild(q)}
   current.appendChild(navigator);
   if(resource&&resource.url&&resource.title){
    var wrap=document.createElement('div');wrap.className='lah-rn-resource-block';
    if(intro){var p=document.createElement('p');p.className='lah-rn-resource-intro';p.textContent=intro;wrap.appendChild(p)}
    var a=document.createElement('a');a.className='lah-rn-resource';a.href=resource.url;a.textContent=resource.title;a.target='_blank';a.rel='noopener';wrap.appendChild(a);current.appendChild(wrap);
   } else if(accessIntro){
    var access=document.createElement('div');access.className='lah-rn-access-intro';var ap=document.createElement('p');ap.textContent=accessIntro;access.appendChild(ap);current.appendChild(access);
   }
   current.scrollTop=current.scrollHeight;
  }
  function showPendingVisitorMessage(message){
   if(pendingVisitorMessage) pendingVisitorMessage.remove();
   pendingVisitorMessage=document.createElement('div');
   pendingVisitorMessage.className='lah-rn-message lah-rn-message--visitor lah-rn-message--pending';
   renderText(pendingVisitorMessage,message,'visitor');
   current.appendChild(pendingVisitorMessage);
   current.scrollTop=current.scrollHeight;
  }

  function showUnitActions(summary){
   actions.innerHTML='';actions.hidden=false;form.hidden=false;
   input.value='';input.placeholder=nextJunctionNudge();
   var label=document.createElement('p');label.className='lah-rn-unit-label';label.textContent='Something has come together here.';actions.appendChild(label);
   if(summary){var p=document.createElement('p');p.className='lah-rn-junction-summary';p.textContent=summary;actions.appendChild(p)}
   var row=document.createElement('div');row.className='lah-rn-unit-buttons';
   var cont=document.createElement('button');cont.type='button';cont.className='lah-rn-primary-secondary';cont.textContent='Continue exploring';
   var stop=document.createElement('button');stop.type='button';stop.className='lah-rn-secondary';stop.textContent='Bring this conversation to a close';
   row.appendChild(cont);row.appendChild(stop);actions.appendChild(row);
   cont.addEventListener('click',function(){
    segmentIndex+=1;segmentOpening=summary||junctionSummary||'';junctionSummary='';
    actions.hidden=true;actions.innerHTML='';form.hidden=false;input.value='';input.placeholder=ordinaryInputPlaceholder();
    setTimeout(function(){input.focus()},120);
   });
   stop.addEventListener('click',function(){endJourney()});
  }
  function endJourney(){
   if(loading||finalizing)return;
   finalizing=true;setLoading(true);input.value='';form.hidden=true;actions.hidden=true;actions.innerHTML='';
   var payload={message:'[Visitor chose to bring this conversation to a close.]',question:originalQuestion||guideSeed||'',original_question:originalQuestion||guideSeed||'',guide_question:originalQuestion||guideSeed||'',journey_action:'end',conversation:contextText(),full_conversation:fullConversationText(),visitor_history:visitorHistoryText(),safety_stage:safetyStage,safety_question:safetyQuestion,country:country,unit_turns:unitTurns,session_id:journeySession,segment_index:segmentIndex,segment_opening:segmentOpening};
   fetch(LAHRN.endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-WP-Nonce':LAHRN.nonce},body:JSON.stringify(payload)})
   .then(function(r){return r.text().then(function(text){var d=null;try{d=text?JSON.parse(text):null}catch(e){throw new Error('The final synthesis could not be prepared right now.')}if(!r.ok)throw new Error(d&&d.message?d.message:'The final synthesis could not be prepared right now.');if(!d)throw new Error('The final synthesis could not be prepared right now.');return d})})
   .then(function(d){
    if(d.journey_synthesis)journeySynthesis=String(d.journey_synthesis);
    var synth=String(d.response||journeySynthesis||'').trim();
    turns.push({role:'navigator',text:synth});
    current.innerHTML='';
    var box=document.createElement('div');box.className='lah-rn-message lah-rn-message--navigator lah-rn-journey-synthesis';
    var title=document.createElement('p');title.className='lah-rn-record-label';title.textContent='What became clearer';box.appendChild(title);
    renderText(box,synth,'navigator');current.appendChild(box);current.scrollTop=current.scrollHeight;
    form.hidden=true;actions.hidden=true;input.disabled=true;
    recordAvailable=true;updateRecordTools();
    returnCompletedJourneyToGuide('',d);
   })
   .catch(function(err){form.hidden=true;var error=document.createElement('div');error.className='lah-rn-message lah-rn-message--navigator';renderText(error,err.message||'Something interrupted the final synthesis.','navigator');current.appendChild(error)})
   .finally(function(){finalizing=false;setLoading(false);updateRecordTools()});
  }
  function updateRecordTools(){recordTools.hidden=!recordAvailable}
  function renderRecord(){
   recordBody.innerHTML='';
   turns.forEach(function(t){
    var block=document.createElement('div');block.className='lah-rn-record-turn lah-rn-record-turn--'+t.role;
    var label=document.createElement('div');label.className='lah-rn-record-label';label.textContent=t.role==='visitor'?'You':'Seeing the Relationship';block.appendChild(label);
    renderText(block,t.text,t.role);recordBody.appendChild(block);
   });
   if(journeySynthesis){
    var synthesisBlock=document.createElement('div');synthesisBlock.className='lah-rn-record-turn lah-rn-record-turn--synthesis';
    var synthesisLabel=document.createElement('div');synthesisLabel.className='lah-rn-record-label';synthesisLabel.textContent='Journey synthesis';synthesisBlock.appendChild(synthesisLabel);
    renderText(synthesisBlock,journeySynthesis,'navigator');recordBody.appendChild(synthesisBlock);
   }
  }
  function openRecord(){renderRecord();record.hidden=false;recordTools.hidden=true}
  function closeRecord(){record.hidden=true;recordTools.hidden=false}
  function printRecord(){
   if(!recordAvailable||!turns.length)return;
   renderRecord();
   var printWindow=window.open('', '_blank', 'width=900,height=700');
   if(!printWindow){
    document.documentElement.classList.add('lah-rn-printing');
    var cleanup=function(){document.documentElement.classList.remove('lah-rn-printing');window.removeEventListener('afterprint',cleanup)};
    window.addEventListener('afterprint',cleanup);
    window.print();
    return;
   }
   var title='Seeing the Relationship — Conversation';
   var styles='body{margin:0;padding:36px;font-family:Arial,Helvetica,sans-serif;color:#222;background:#fff}h1{font-size:24px;margin:0 0 24px;color:#111}.lah-rn-record-body{display:grid;gap:18px}.lah-rn-record-turn{padding:16px;border-radius:12px;line-height:1.65;break-inside:avoid;page-break-inside:avoid}.lah-rn-record-turn--visitor{background:#f1f1f1;border:1px solid #ddd}.lah-rn-record-turn--navigator{background:#fff;border:1px solid #d8d8d8}.lah-rn-record-turn--synthesis{background:#f8f8f8;border:1px solid #cfcfcf}.lah-rn-record-label{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#777;margin-bottom:7px}.lah-rn-record-turn p{margin:0 0 14px}.lah-rn-record-turn p:last-child{margin-bottom:0}@media print{body{padding:20px}}';
   var html='<!doctype html><html><head><meta charset=\"utf-8\"><title>'+title+'</title><style>'+styles+'</style></head><body><h1>Seeing the Relationship</h1><div class=\"lah-rn-record-body\">'+recordBody.innerHTML+'</div></body></html>';
   printWindow.document.open();
   printWindow.document.write(html);
   printWindow.document.close();
   var doPrint=function(){
    try{printWindow.focus();printWindow.print();}finally{setTimeout(function(){try{printWindow.close()}catch(e){}},500)}
   };
   if(printWindow.document.fonts&&printWindow.document.fonts.ready){printWindow.document.fonts.ready.then(function(){setTimeout(doPrint,150)}).catch(function(){setTimeout(doPrint,250)});}else{setTimeout(doPrint,300);}
  }
  var waitTimerSlow=null;
  var waitTimerLong=null;

  function clearWaitTimers(){
   if(waitTimerSlow){window.clearTimeout(waitTimerSlow);waitTimerSlow=null;}
   if(waitTimerLong){window.clearTimeout(waitTimerLong);waitTimerLong=null;}
  }

  function ensureWaitState(){
   var state=current.querySelector('.lah-rn-wait-state');
   if(state)return state;
   state=document.createElement('div');
   state.className='lah-rn-wait-state';
   state.setAttribute('role','status');
   state.setAttribute('aria-live','polite');
   var spinner=document.createElement('span');
   spinner.className='lah-rn-wait-spinner';
   spinner.setAttribute('aria-hidden','true');
   var text=document.createElement('span');
   text.className='lah-rn-wait-text';
   state.appendChild(spinner);
   state.appendChild(text);
   current.appendChild(state);
   return state;
  }

  function showWaitState(message){
   var state=ensureWaitState();
   var text=state.querySelector('.lah-rn-wait-text');
   if(text)text.textContent=String(message||'Taking a moment with this…');
   state.hidden=false;
   current.scrollTop=current.scrollHeight;
   clearWaitTimers();
   waitTimerSlow=window.setTimeout(function(){
    if(!loading)return;
    if(text)text.textContent='Still taking a moment with this…';
   },8000);
   waitTimerLong=window.setTimeout(function(){
    if(!loading)return;
    if(text)text.textContent='This is taking a little longer than usual. The conversation is still being processed.';
   },16000);
  }

  function hideWaitState(){
   clearWaitTimers();
   var state=current.querySelector('.lah-rn-wait-state');
   if(state)state.remove();
  }

  function setLoading(value){
   loading=value;
   root.classList.toggle('is-loading',value);
   submit.disabled=value;
   input.disabled=value;
   // The conversation surface, not the empty composer, is the waiting state.
   // Keep the submitted visitor turn visible while provider work is in flight and
   // reveal the composer only after HRN has returned a completed conversational act.
   if(value){
    form.hidden=true;
    showWaitState(root.classList.contains('is-guide-handoff') ? 'Bringing your question into the conversation…' : 'Taking a moment with this…');
   }else{
    hideWaitState();
   }
 }
  function fullConversationText(){
   return turns.map(function(t){return (t.role==='visitor'?'Visitor: ':'Seeing the Relationship: ')+t.text}).join('\n\n').slice(-50000);
  }
  function contextText(){
   return turns.slice(-8).map(function(t){return (t.role==='visitor'?'Visitor: ':'Seeing the Relationship: ')+t.text}).join('\n\n').slice(-14000);
  }
  function visitorHistoryText(){return turns.filter(function(t){return t.role==='visitor'}).slice(-12).map(function(t){return t.text}).join('\n\n').slice(-12000)}

  function clearSafetyIdle(){if(safetyIdleTimer){window.clearTimeout(safetyIdleTimer);safetyIdleTimer=null}}
  function clearSafetyReveal(){if(safetyRevealTimer){window.clearTimeout(safetyRevealTimer);safetyRevealTimer=null}}
  function armSafetyIdle(stage){
   clearSafetyIdle();
   if(stage!=='acute'&&stage!=='acute_followthrough'&&stage!=='acute_connection'&&stage!=='acute_contact'&&stage!=='acute_barrier'&&stage!=='recovery')return;
   safetyIdleTimer=window.setTimeout(function(){
    if(loading||form.hidden)return;
    var existing=current.querySelector('.lah-rn-safety-idle');
    if(existing)return;
    var n=document.createElement('p');n.className='lah-rn-safety-idle lah-rn-safety-idle--question';n.textContent='Are you still there? You can use the emergency or crisis support above, or tell me what is happening right now.';current.appendChild(n);
   },90000);
  }

  function showSafety(response,visitorText){
   clearSafetyIdle();
   clearSafetyReveal();
   response=response||{};
   var stage=response.stage||response.safety||'current';
   if(response.country)country=String(response.country);
   var message=response.message||response.safety_message||'';
   var question=response.question||response.safety_question||'';
   safetyMessage=message;
   if(question)safetyQuestion=question;
   if(stage)safetyStage=stage;
   var resources=Array.isArray(response.resources)?response.resources:(Array.isArray(response.safety_resources)?response.safety_resources:[]);
   var locationRequired=!!(response.location_required||response.safety_location_required);
   var note=response.note||response.safety_note||'';
   var releaseReady=!!response.safety_release_ready;
   current.innerHTML='';
   if(visitorText){var visitor=document.createElement('div');visitor.className='lah-rn-message lah-rn-message--visitor';renderText(visitor,visitorText,'visitor');current.appendChild(visitor)}
   var box=document.createElement('div');box.className='lah-rn-safety';
   var headings={current:'I want to ask you something directly.',support:'You do not have to carry this alone.',acute:'Please move away from immediate harm',acute_followthrough:'Bring another person into this now if you can',acute_connection:'Stay with the person who is with you',acute_contact:'Please contact emergency or crisis support now',acute_barrier:'Let us find what is making the next safety step difficult',acute_hold:'Please use the emergency or crisis support above now',recovery:'Let us make sure you are safe before we return to anything else.'};
   if(headings[stage]){var heading=document.createElement('h3');heading.textContent=headings[stage];box.appendChild(heading)}
   if(message){var p=document.createElement('p');p.textContent=message;box.appendChild(p)}
   if(question && question.trim() !== message.trim()){var q=document.createElement('p');q.className='lah-rn-question';q.textContent=question;box.appendChild(q)}
   if(locationRequired){
    var loc=document.createElement('div');loc.className='lah-rn-safety-location';
    var lp=document.createElement('p');lp.textContent='Where are you right now? Tell me the country so I can show the local resources I have verified.';loc.appendChild(lp);
    var li=document.createElement('input');li.type='text';li.className='lah-rn-safety-country';li.placeholder='Country';li.setAttribute('aria-label','Country where you are now');loc.appendChild(li);
    var lb=document.createElement('button');lb.type='button';lb.className='lah-rn-primary-secondary';lb.textContent='Show local help';loc.appendChild(lb);
    lb.addEventListener('click',function(){var v=li.value.trim();if(!v)return;country=v;input.value='';form.hidden=true;actions.hidden=true;submitSafetyLocation(v)});
    box.appendChild(loc);
   }
   var resourceWrap=null;
   if(resources.length){
    resourceWrap=document.createElement('div');resourceWrap.className='lah-rn-safety-resource-reveal lah-rn-safety-resource-panel';
    var list=document.createElement('div');list.className='lah-rn-safety-resources';
    var lastGroup='';
    resources.forEach(function(r){
     var group=String(r.group||'').trim();
     if(group&&group!==lastGroup){var gh=document.createElement('h4');gh.className='lah-rn-safety-resource-group';gh.textContent=group;list.appendChild(gh);lastGroup=group}
     var item=document.createElement('div');item.className='lah-rn-safety-resource';
     var title=document.createElement('strong');title.textContent=r.title||'';item.appendChild(title);
     if(r.phone){var a=document.createElement('a');a.href='tel:'+String(r.phone).replace(/[^0-9+]/g,'');var displayPhone=r.display_phone||r.phone;a.textContent=(Array.isArray(r.channels)&&r.channels.indexOf('text')!==-1)?'Call or text '+displayPhone:'Call '+displayPhone;item.appendChild(a)}
     if(r.url){var u=document.createElement('a');u.href=r.url;u.target='_blank';u.rel='noopener';u.textContent=r.link_text||'Open Find A Helpline';item.appendChild(u)}
     if(r.hours){var small=document.createElement('span');small.textContent=r.hours;item.appendChild(small)}
     list.appendChild(item);
    });
    resourceWrap.appendChild(list);
    if(note){var noteEl=document.createElement('p');noteEl.className='lah-rn-safety-note';noteEl.textContent=note;resourceWrap.appendChild(noteEl)}
    box.appendChild(resourceWrap);
   } else if(note){var noteEl=document.createElement('p');noteEl.className='lah-rn-safety-note';noteEl.textContent=note;box.appendChild(noteEl)}
   current.appendChild(box);
   if(resourceWrap && (stage==='acute'||stage==='acute_followthrough'||stage==='acute_contact'||stage==='acute_barrier')){
    resourceWrap.hidden=true;
    safetyRevealTimer=window.setTimeout(function(){resourceWrap.hidden=false;resourceWrap.classList.add('is-revealed')},7000);
   }


   if(releaseReady){
    form.hidden=true;actions.innerHTML='';actions.hidden=false;
    var releaseRow=document.createElement('div');releaseRow.className='lah-rn-unit-buttons';
    var cont=document.createElement('button');cont.type='button';cont.className='lah-rn-primary-secondary';cont.textContent='Return to the conversation';
    var stop=document.createElement('button');stop.type='button';stop.className='lah-rn-secondary';stop.textContent='Stop here';
    releaseRow.appendChild(cont);releaseRow.appendChild(stop);actions.appendChild(releaseRow);
    cont.addEventListener('click',function(){clearSafetyIdle();safetyStage='green';safetyQuestion='';actions.innerHTML='';actions.hidden=true;current.innerHTML='';form.hidden=false;input.value='';input.placeholder=ordinaryInputPlaceholder();setTimeout(function(){input.focus()},120)});
    stop.addEventListener('click',function(){actions.innerHTML='';var label=document.createElement('p');label.className='lah-rn-unit-label';label.textContent='You can leave the conversation here.';actions.appendChild(label);form.hidden=true});
    return;
   }
   if(question){form.hidden=false;input.value='';input.placeholder='Answer in your own words.';setTimeout(function(){input.focus()},120);armSafetyIdle(stage)}else{form.hidden=true;armSafetyIdle(stage)}
  }
  function submitSafetyLocation(v){
   setLoading(true);
   fetch(LAHRN.emergency_endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-WP-Nonce':LAHRN.nonce},body:JSON.stringify({country:v,safety_stage:safetyStage,safety_question:safetyQuestion,safety_message:safetyMessage})})
   .then(function(r){return r.text().then(function(text){var d=null;try{d=text?JSON.parse(text):null}catch(e){throw new Error('The server returned an unexpected response (HTTP '+r.status+').')}if(!r.ok)throw new Error(d&&d.message?d.message:'The local resource request could not be completed.');if(!d)throw new Error('The server returned an empty response (HTTP '+r.status+').');return d})})
   .then(function(d){
    if(d.operation!=='resource_location_resolution')throw new Error('The server returned an unexpected resource response.');
    country=d.country||v;
    safetyStage=d.stage||safetyStage;
    safetyQuestion=d.question||safetyQuestion;
    safetyMessage=d.message||safetyMessage;
    showSafety(d,'');
   })
   .catch(function(){current.innerHTML='';var e=document.createElement('div');e.className='lah-rn-safety';renderText(e,'I could not load the local resource list right now. If you may be in immediate danger, contact the emergency service where you are or go to the nearest emergency department, and stay with another person.','navigator');current.appendChild(e)})
   .finally(function(){setLoading(false)})
  }

  function returnCompletedJourneyToGuide(message,d){
   if(guideReturnPending||guideReturnComplete||typeof LAHRN==='undefined')return;
   if(!d||!d.unit_complete||d.synthesis_mode!=='whole_journey')return;
   // The WordPress adapter is the sole server-to-server caller of USE.
   // Consume its already validated response; never send visitor transcripts
   // directly from the browser to the public Render endpoint.
   guideReturnPending=true;
   var doorway=d.canonical_doorway;
   if(!doorway||!doorway.url||!doorway.title){
    var status=String(d.return_handoff_status||'');
    var noFit=status==='no_grounded_doorway';
    var note=document.createElement('p');
    note.className='lah-rn-access-intro'+(noFit?' lah-rn-guide-no-fit':'');
    note.textContent=String(d.return_handoff_response||(noFit?'No canonical doorway was close enough to offer honestly from this conversation.':'The conversation can rest here. The Archive doorway is not available right now.')).trim();
    current.appendChild(note);
    current.scrollTop=current.scrollHeight;
    recordAvailable=true;updateRecordTools();
    if(noFit)guideReturnComplete=true;
    guideReturnPending=false;
    return;
   }
   var wrap=document.createElement('div');wrap.className='lah-rn-resource-block lah-rn-resource-block--guide';
   var p=document.createElement('p');p.className='lah-rn-resource-intro';p.textContent='A place in the Archive that may carry this further:';wrap.appendChild(p);
   var a=document.createElement('a');a.className='lah-rn-resource';a.href=doorway.url;a.textContent=doorway.title;a.target='_blank';a.rel='noopener';wrap.appendChild(a);
   current.appendChild(wrap);
   current.scrollTop=current.scrollHeight;
   recordAvailable=true;updateRecordTools();
   guideReturnComplete=true;
   guideReturnPending=false;
  }
  function beginGuideHandoff(){
   if(!guideSeed||loading)return;
   originalQuestion=guideSeed;
   // The forwarded seed belongs to the conversation transcript, not the
   // editable composer. Keeping it out of the textarea prevents the old
   // double-entry state while preserving immediate visual feedback.
   input.value='';
   current.innerHTML='';
   pendingHandoffVisitor=document.createElement('div');
   pendingHandoffVisitor.className='lah-rn-message lah-rn-message--visitor lah-rn-handoff-preview';
   renderText(pendingHandoffVisitor,guideSeed,'visitor');
   current.appendChild(pendingHandoffVisitor);
   current.scrollTop=current.scrollHeight;
   input.disabled=true;
   submit.disabled=true;
   root.classList.add('is-guide-handoff');
   if(handoffStatus){handoffStatus.hidden=false;handoffStatus.textContent='Bringing your question into the conversation…';}
   showWaitState('Bringing your question into the conversation…');
   var label=submit.querySelector('.lah-rn-button-label');
   if(label)label.textContent='Entering';
   input.setAttribute('aria-busy','true');
  }

  function submitMessage(forcedMessage){
   var message=(typeof forcedMessage==='string'?forcedMessage:input.value).trim();if(!message||loading)return;
   if(!originalQuestion)originalQuestion=message;
   setLoading(true);
   // Preserve the visitor's submitted turn visibly while the server is working.
   // The editable field may clear for the next turn, but the conversation must
   // never appear to lose the visitor's message during a slow provider response.
   if(!guideSeed && turns.length) showPendingVisitorMessage(message);
   if(!guideSeed||turns.length) input.value='';
   input.setAttribute('aria-busy','true');
   fetch(LAHRN.endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-WP-Nonce':LAHRN.nonce},body:JSON.stringify({message:message,original_question:originalQuestion||message,guide_question:originalQuestion||'',conversation:contextText(),full_conversation:fullConversationText(),visitor_history:visitorHistoryText(),safety_stage:safetyStage,safety_question:safetyQuestion,country:country,unit_turns:unitTurns,session_id:journeySession,segment_index:segmentIndex,segment_opening:segmentOpening})})
   .then(function(r){return r.text().then(function(text){var d=null;try{d=text?JSON.parse(text):null}catch(e){throw new Error('The server returned an unexpected response (HTTP '+r.status+').')}if(!r.ok)throw new Error(d&&d.message?d.message:'The conversation could not continue.');if(!d)throw new Error('The server returned an empty response (HTTP '+r.status+').');return d})})
   .then(function(d){
    d=normalizeResponseEnvelope(d);
    // Visitor-surface invariant: provider/transport envelopes must never be rendered
    // as conversational prose. A malformed nested envelope is a recoverable server
    // composition failure, not content for the visitor to see.
    if(responseLooksLikeEnvelope(d&&d.response))throw new Error('The conversation could not be composed right now. Please try again.');
    if(d.safety_interrupt){
     turns.push({role:'visitor',text:message});
     var safetyMessage=d.safety_message||'';var safetyQuestionText=d.safety_question||'';var safetyText=safetyMessage;if(safetyQuestionText&&safetyQuestionText.trim()!==safetyMessage.trim())safetyText+=(safetyText?'\n\n':'')+safetyQuestionText;
     turns.push({role:'navigator',text:safetyText});if(guideSeed)clearGuideHandoffState();safetyStage=d.safety||'current';safetyQuestion=safetyQuestionText;showSafety(d,message);recordAvailable=true;updateRecordTools();return;
    }
    if(d.safety && d.safety !== 'green'){
     turns.push({role:'visitor',text:message});
     var guardedMessage=d.safety_message||'';var guardedQuestion=d.safety_question||'';var guardedText=guardedMessage;if(guardedQuestion&&guardedQuestion.trim()!==guardedMessage.trim())guardedText+=(guardedText?'\n\n':'')+guardedQuestion;
     turns.push({role:'navigator',text:guardedText});if(guideSeed)clearGuideHandoffState();safetyStage=d.safety;safetyQuestion=guardedQuestion;showSafety(d,message);recordAvailable=true;updateRecordTools();return;
    }
    safetyStage='green';safetyQuestion='';
    if(guideSeed){clearGuideHandoffState();}var activeLabel=submit.querySelector('.lah-rn-button-label');if(activeLabel)activeLabel.textContent='Continue';
    if(d.journey_ledger){
     var jl=d.journey_ledger;
     threadSummary=String(jl.journey_purpose||threadSummary);perspectiveDelta=String(jl.perspective_delta||perspectiveDelta);unresolved=String(jl.unresolved||unresolved);bodyOfThought=String(jl.body_of_thought||bodyOfThought);newTerrain=String(jl.new_terrain||newTerrain);nextHorizon=String(jl.next_horizon||nextHorizon);fractalStage=String(jl.fractal_stage||fractalStage);fractalMaturity=String(jl.fractal_maturity||fractalMaturity);pivotSignal=String(jl.pivot_signal||pivotSignal);leadershipNeed=String(jl.leadership_need||leadershipNeed);currentFractal=String(jl.current_terrain||currentFractal);resourceFit=String(jl.resource_fit||resourceFit);
    }
    unitTurns=Number(d.journey_turn||d.unit_position||unitTurns||0);
    threadSummary=String(d.thread_summary||threadSummary);workingHypothesis=String(d.working_hypothesis||workingHypothesis);unresolved=String(d.unresolved||unresolved);
    underlyingNeed=String(d.underlying_need||underlyingNeed);desiredCondition=String(d.desired_condition||desiredCondition);emergingDelta=String(d.emerging_delta||emergingDelta);perspectiveDelta=String(d.perspective_delta||perspectiveDelta);bodyOfThought=String(d.body_of_thought||bodyOfThought);movementDirection=String(d.movement_direction||movementDirection);nextMovement=String(d.next_movement||nextMovement);resourceFit=String(d.resource_fit||resourceFit);
    fractalStage=String(d.fractal_stage||fractalStage);fractalTransition=String(d.fractal_transition||fractalTransition);newTerrain=String(d.new_terrain||newTerrain);completedInsight=String(d.completed_insight||completedInsight);nextHorizon=String(d.next_horizon||nextHorizon);conversationPurpose=String(d.conversation_purpose||conversationPurpose);currentFractal=String(d.current_fractal||currentFractal);fractalMaturity=String(d.fractal_maturity||fractalMaturity);pivotSignal=String(d.pivot_signal||pivotSignal);leadershipNeed=String(d.leadership_need||leadershipNeed);
    if(d.journey_synthesis) journeySynthesis=String(d.journey_synthesis);
    if(d.junction_summary) junctionSummary=String(d.junction_summary);
    if(d.journey_ledger && d.journey_ledger.last_fractal_summary) junctionSummary=String(d.journey_ledger.last_fractal_summary);
    if(d.journey_ledger && Array.isArray(d.journey_ledger.fractal_records)) fractalHistory=d.journey_ledger.fractal_records.slice();
    if(d.error_type==='retryable_operation_failure'||d.retryable===true){
     var retryMessage=String(d.message||'The conversation could not continue right now. Please try again.');
     var retryEl=document.createElement('div');retryEl.className='lah-rn-message lah-rn-message--navigator lah-rn-retry-notice';renderText(retryEl,retryMessage,'navigator');current.appendChild(retryEl);
     current.scrollTop=current.scrollHeight;
     if(guideSeed)clearGuideHandoffState();
     pendingHandoffVisitor=null;
     form.hidden=false;actions.hidden=true;input.disabled=false;submit.disabled=false;input.removeAttribute('aria-busy');input.placeholder=ordinaryInputPlaceholder();
     setTimeout(function(){input.focus()},120);return;
    }
    var response=String(d.response||'').trim();if(!response)throw new Error('The server returned no conversational response for this operation.');var question=String(d.question||'').trim();var resource=(Array.isArray(d.resources)&&d.resources.length)?d.resources[0]:null;var complete=!!d.unit_complete;var accessIntro=String(d.access_intro||'').trim();
    turns.push({role:'visitor',text:message});
    turns.push({role:'navigator',text:response+(question?'\n\n'+question:'')+(d.resource_intro?'\n\n'+d.resource_intro:'')+(resource&&resource.title?'\n'+resource.title:'')+(accessIntro?'\n\n'+accessIntro:'')});
    current.innerHTML='';
    pendingVisitorMessage=null;
    appendCurrent(message,response,question,resource,String(d.resource_intro||''),accessIntro);
    if(journeySynthesis&&d.synthesis_mode==='whole_journey'){
     var synthesisVisible=document.createElement('div');synthesisVisible.className='lah-rn-message lah-rn-message--navigator lah-rn-journey-synthesis';
     var synthesisTitle=document.createElement('p');synthesisTitle.className='lah-rn-record-label';synthesisTitle.textContent='Journey synthesis';synthesisVisible.appendChild(synthesisTitle);
     renderText(synthesisVisible,journeySynthesis,'navigator');current.appendChild(synthesisVisible);current.scrollTop=current.scrollHeight;
    }
    recordAvailable=true;
    if(d.junction_available){
     showUnitActions(String(d.junction_summary||junctionSummary||''));
    }else{
     actions.hidden=true;
     form.hidden=false;
     input.placeholder=ordinaryInputPlaceholder();
     setTimeout(function(){input.focus()},120);
    }
    updateRecordTools();
   })
   .catch(function(err){
    var failedQuestion=String(guideSeed||originalQuestion||message||'').trim();
    hideWaitState();
    if(guideSeed){
     root.classList.remove('is-guide-handoff');
     if(handoffStatus)handoffStatus.hidden=true;
     if(pendingHandoffVisitor){
      pendingHandoffVisitor.classList.remove('lah-rn-handoff-preview');
      pendingHandoffVisitor.classList.add('lah-rn-message--failed-handoff');
     }else if(failedQuestion){
      var preserved=document.createElement('div');
      preserved.className='lah-rn-message lah-rn-message--visitor lah-rn-message--failed-handoff';
      renderText(preserved,failedQuestion,'visitor');
      current.insertBefore(preserved,current.firstChild||null);
     }
     pendingHandoffVisitor=null;
     guideSeed='';
     originalQuestion='';
    }else{
     pendingHandoffVisitor=null;
     input.value='';
     input.removeAttribute('aria-busy');
     input.placeholder=ordinaryInputPlaceholder();
    }
    input.disabled=false;
    submit.disabled=false;
    form.hidden=false;
    input.removeAttribute('aria-busy');
    input.placeholder=ordinaryInputPlaceholder();
    var error=document.createElement('div');
    error.className='lah-rn-message lah-rn-message--navigator lah-rn-retry-notice';
    renderText(error,err.message||'Something interrupted the conversation. Please try again.','navigator');
    current.appendChild(error);
    current.scrollTop=current.scrollHeight;
   })
   .finally(function(){setLoading(false);input.removeAttribute('aria-busy');updateRecordTools()})
  }
  form.addEventListener('submit',function(e){e.preventDefault();submitMessage()});
  if(guideSeed){
   beginGuideHandoff();
   var handoffMessage=guideSeed;
   setTimeout(function(){submitMessage(handoffMessage)},180);
  }
  viewRecord&&viewRecord.addEventListener('click',openRecord);recordClose&&recordClose.addEventListener('click',closeRecord);printButton&&printButton.addEventListener('click',printRecord);
 });
});
})();

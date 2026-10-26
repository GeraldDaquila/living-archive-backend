<?php
/**
 * Plugin Name: CLSS Guided Reflection
 * Description: Private, session-only guided reflection with separate self and third-party perspectives.
 * Version: 0.2.0
 * Author: Living Archive
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'clss_guided_reflection_prototype', 'clss_grp_render_v2' );

function clss_grp_render_v2() {
    static $rendered = false;
    if ( $rendered ) {
        return '<p class="clss-dp-small">The CLSS reflection can appear only once on a page.</p>';
    }
    $rendered = true;

    wp_register_style( 'clss-grp-style-v2', false, array(), '0.2.0' );
    wp_enqueue_style( 'clss-grp-style-v2' );
    wp_add_inline_style( 'clss-grp-style-v2', '
#clss-diagnostic-prototype{width:100%;max-width:650px;margin:0 auto;color:#222;font-family:inherit;line-height:1.6}
#clss-diagnostic-prototype *{box-sizing:border-box}
#clss-diagnostic-prototype .clss-dp-kicker{font-size:.78rem;letter-spacing:.07em;text-transform:uppercase;color:#666}
#clss-diagnostic-prototype h2{font-size:clamp(1.45rem,3.4vw,1.9rem);line-height:1.3;margin:.5rem 0 1rem;font-weight:600}
#clss-diagnostic-prototype h3{font-size:1.1rem;line-height:1.4;margin:1.25rem 0 .5rem}
#clss-diagnostic-prototype .clss-dp-panel{border:1px solid #dedede;border-radius:18px;padding:clamp(20px,4vw,32px);margin:18px 0;background:#f2f2f2}
#clss-diagnostic-prototype .clss-dp-progress{height:5px;background:#e5e5e5;border-radius:9px;overflow:hidden;margin:16px 0 24px}
#clss-diagnostic-prototype .clss-dp-progress span{display:block;height:100%;width:0;background:#222;transition:width .2s}
#clss-diagnostic-prototype label{display:block;font-weight:600;margin:12px 0 8px}
#clss-diagnostic-prototype textarea{display:block;width:100%;border:1px solid #ccc;border-radius:14px;padding:16px;background:#fff;color:#222;font:inherit;min-height:130px;box-shadow:none}
#clss-diagnostic-prototype button{border:1px solid #000;border-radius:12px;padding:10px 16px;background:#000;color:#fff;font:inherit;font-size:.94rem;line-height:1.35;cursor:pointer}
#clss-diagnostic-prototype button.secondary{background:#fff;color:#222}
#clss-diagnostic-prototype button:disabled{opacity:.45;cursor:not-allowed}
#clss-diagnostic-prototype .clss-dp-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
#clss-diagnostic-prototype .clss-dp-small{font-size:.92rem;color:#5d5d5d}
#clss-diagnostic-prototype .clss-dp-note{border-left:3px solid #777;padding-left:12px}
#clss-diagnostic-prototype [hidden]{display:none!important}
#clss-diagnostic-prototype a{color:inherit;text-decoration:underline}
@media print{body *{visibility:hidden!important}#clss-diagnostic-prototype .clss-dp-result,#clss-diagnostic-prototype .clss-dp-result *{visibility:visible!important}#clss-diagnostic-prototype .clss-dp-result{display:block!important;position:absolute!important;left:0!important;top:0!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;background:#fff!important;color:#111!important}#clss-diagnostic-prototype .clss-dp-result .clss-dp-actions{display:none!important}}
' );

    wp_register_script( 'clss-grp-script-v2', false, array(), '0.2.0', true );
    wp_enqueue_script( 'clss-grp-script-v2' );
    wp_add_inline_script( 'clss-grp-script-v2', '
(function(){
  var root=document.getElementById("clss-diagnostic-prototype");
  if(!root||root.dataset.ready==="1")return;
  root.dataset.ready="1";

  var prompts={
    self:[
      ["What responsibility or decision am I facing?","State the decision or role, why it matters now, and what is within my control."],
      ["What examples support my current view of my own leadership?","Separate what I directly did or observed, what others told me, documented outcomes, and what I think it may mean."],
      ["How do I respond when resources are scarce or priorities conflict?","Recall a specific trade-off, what I chose, who was affected, and what followed."],
      ["What do I do when I receive difficult feedback?","Use an example. Consider whether I listened, asked questions, took responsibility, made repairs, became defensive, or avoided the issue."],
      ["What effects do my choices have on other people and how the work gets done?","Consider trust, clarity, fairness, capability, and longer-term effects, including effects I did not intend."],
      ["What do my actions around authority and responsibility show—and what do I not yet know?","Describe actions and results. Do not treat confidence, ambition, hesitation, or reluctance as proof of motive."],
      ["Have I freely accepted this responsibility, and do the people affected understand the arrangement?","Consider willingness, relevant consent, expectations, and whether concerns can be raised safely."],
      ["Are my authority, responsibilities, support, and review date clear?","Identify what I may decide, my limits, where feedback can go, what support is available, and when the arrangement will be reviewed."],
      ["What still needs to be checked before I make or accept this decision?","Name the most important information gap and a fair, practical way to examine it."]
    ],
    third_party:[
      ["What decision about this person's role are we facing?","State the decision, the role, why it matters now, and who is affected."],
      ["What examples support my current view of this person's leadership?","Separate what I directly observed, documented outcomes, what others reported, reputation, and my own interpretation."],
      ["How does this person respond when resources are scarce or priorities conflict?","Recall a specific trade-off, what they chose, who was affected, and what followed. Note what I saw myself versus what I was told."],
      ["What happens when this person receives difficult feedback?","Look for specific examples of listening, clarification, taking responsibility, repair, retaliation, or repeated avoidance. One event alone does not establish a pattern."],
      ["What effects does this person's leadership have on other people and how the work gets done?","Consider trust, clarity, fairness, capability, and longer-term effects. Other conditions may also help explain what happened."],
      ["What do this person's actions around authority and responsibility show—and what remains unknown?","Describe actions and results. Do not state assumed motives or private thoughts as facts."],
      ["Is this responsibility being freely accepted and understood by the people affected?","Consider the person's expressed willingness, relevant consent, clear expectations, and whether people can raise concerns safely."],
      ["Are the role's authority, responsibilities, support, and review date clear?","Identify what the person may decide, the limits, feedback channels, support, and agreed review point."],
      ["What still needs to be checked before a responsible decision can be made?","Name the most important information gap and the fairest practical way to examine it."]
    ]
  };

  var state={perspective:"",answers:[],index:0};
  var intro=root.querySelector("[data-screen=intro]");
  var question=root.querySelector("[data-screen=question]");
  var result=root.querySelector("[data-screen=result]");
  var title=root.querySelector("[data-question-title]");
  var help=root.querySelector("[data-question-help]");
  var kicker=root.querySelector("[data-kicker]");
  var bar=root.querySelector("[data-progress]");
  var input=root.querySelector("[data-answer]");
  var perspectiveLabel=root.querySelector("[data-perspective-label]");
  var summary=root.querySelector("[data-summary]");

  function promptsForMode(){return prompts[state.perspective]||[];}
  function show(which){
    intro.hidden=which!=="intro";
    question.hidden=which!=="question";
    result.hidden=which!=="result";
  }
  function safeText(value){
    return String(value).replace(/[&<>"\x27]/g,function(ch){
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","\x27":"&#39;"}[ch];
    });
  }
  function renderQuestion(){
    var list=promptsForMode(),item=list[state.index];
    kicker.textContent="Question "+(state.index+1)+" of "+list.length;
    title.textContent=item[0];
    help.textContent=item[1];
    perspectiveLabel.textContent=state.perspective==="self"?"Self-reflection":"Reflection on another person's leadership";
    input.value=state.answers[state.index]||"";
    bar.style.width=((state.index+1)/list.length*100)+"%";
    question.querySelector("[data-back]").disabled=state.index===0;
    question.querySelector("[data-next]").textContent=state.index===list.length-1?"Review my notes":"Next";
  }
  function capture(){state.answers[state.index]=input.value;}
  function buildResult(){
    var list=promptsForMode(),answered=0,html="";
    list.forEach(function(item,i){if((state.answers[i]||"").trim())answered++;});
    html+="<p><strong>Notes entered:</strong> "+answered+" of "+list.length+" areas.</p>";
    if(answered===0){
      html+="<p>No examples were entered. There is not enough information here to draw a fair conclusion.</p>";
    } else {
      html+="<h3>What you recorded</h3><ol>";
      list.forEach(function(item,i){
        var answer=(state.answers[i]||"").trim();
        if(answer)html+="<li><strong>"+safeText(item[0])+"</strong><p>"+safeText(answer).replace(/\n/g,"<br>")+"</p></li>";
      });
      html+="</ol>";
    }
    var missing=list.filter(function(item,i){return !(state.answers[i]||"").trim();});
    if(missing.length){
      html+="<h3>What remains unknown</h3><ul>";
      missing.forEach(function(item){html+="<li>"+safeText(item[0])+"</li>";});
      html+="</ul><p>A blank answer is missing information, not evidence against anyone.</p>";
    }
    html+="<h3>A careful next step</h3><p>Choose one important point from these notes. If it could affect another person or a significant decision, check it with another source or ask a fair, open question. Consider another possible explanation before deciding what it means.</p>";
    html+="<p class=\"clss-dp-note\">This page organizes the notes you entered. It does not independently verify them, determine anyone's motives, score leadership, or decide whether someone should be appointed. Do not use this reflection alone to make a hiring, promotion, or removal decision.</p>";
    html+="<h3>Where to go next</h3><p>No resource is selected automatically. Use a CLSS resource only after you have identified a specific question that it can help you examine.</p>";
    summary.innerHTML=html;
    perspectiveLabel.textContent=state.perspective==="self"?"Self-reflection":"Reflection on another person's leadership";
  }

  root.querySelectorAll("[data-choose-perspective]").forEach(function(button){
    button.addEventListener("click",function(){
      var mode=button.getAttribute("data-choose-perspective");
      if(mode!=="self"&&mode!=="third_party")return;
      state={perspective:mode,answers:new Array(9).fill(""),index:0};
      show("question");
      renderQuestion();
      input.focus();
    });
  });
  root.querySelector("[data-next]").addEventListener("click",function(){
    capture();
    if(state.index<promptsForMode().length-1){state.index++;renderQuestion();input.focus();}
    else{buildResult();show("result");root.querySelector("[data-restart]").focus();}
  });
  root.querySelector("[data-back]").addEventListener("click",function(){
    capture();
    if(state.index>0){state.index--;renderQuestion();input.focus();}
  });
  root.querySelector("[data-skip]").addEventListener("click",function(){
    state.answers[state.index]="";
    if(state.index<promptsForMode().length-1){state.index++;renderQuestion();input.focus();}
    else{buildResult();show("result");root.querySelector("[data-restart]").focus();}
  });
  root.querySelector("[data-restart]").addEventListener("click",function(){
    state={perspective:"",answers:[],index:0};
    input.value="";
    summary.innerHTML="";
    bar.style.width="0";
    show("intro");
    root.querySelector("[data-choose-perspective]").focus();
  });
  root.querySelector("[data-print]").addEventListener("click",function(){window.print();});
})();
' );

    return '<div id="clss-diagnostic-prototype" class="clss-dp">
<section class="clss-dp-panel" data-screen="intro">
  <div class="clss-dp-kicker">CLSS · Guided reflection</div>
  <h2>See the situation more clearly before deciding what it means.</h2>
  <p>This guided reflection helps you organize examples about leadership, responsibility, and how decisions affect people. It does not score a person or decide whether someone should be appointed.</p>
  <p class="clss-dp-small">Your answers stay in this page session. They are not submitted to a server. Use examples where possible, and separate what you observed from what you heard or think it may mean.</p>
  <h3>Choose the kind of reflection</h3>
  <div class="clss-dp-actions">
    <button type="button" data-choose-perspective="self">Reflect on my own leadership</button>
    <button type="button" class="secondary" data-choose-perspective="third_party">Reflect on another person’s leadership</button>
  </div>
</section>
<section class="clss-dp-panel" data-screen="question" hidden>
  <div class="clss-dp-kicker" data-kicker>Question 1 of 9</div>
  <p class="clss-dp-small" data-perspective-label></p>
  <div class="clss-dp-progress" aria-hidden="true"><span data-progress></span></div>
  <h2 data-question-title></h2>
  <p data-question-help class="clss-dp-small"></p>
  <label for="clss-dp-answer">Your notes</label>
  <textarea id="clss-dp-answer" data-answer placeholder="Describe a specific example, what happened, and what information you have." rows="5"></textarea>
  <p class="clss-dp-small">If you do not know, leave this blank. Missing information is not proof of a problem.</p>
  <div class="clss-dp-actions">
    <button type="button" class="secondary" data-back>Back</button>
    <button type="button" data-next>Next</button>
    <button type="button" class="secondary" data-skip>Mark as unknown</button>
  </div>
</section>
<section class="clss-dp-panel clss-dp-result" data-screen="result" hidden>
  <div class="clss-dp-kicker">Your reflection summary</div>
  <p class="clss-dp-small" data-perspective-label></p>
  <h2>What have you recorded, and what remains unclear?</h2>
  <div data-summary></div>
  <div class="clss-dp-actions">
    <button type="button" data-restart>Start again</button>
    <button type="button" class="secondary" data-print>Print summary</button>
  </div>
</section>
</div>';
}

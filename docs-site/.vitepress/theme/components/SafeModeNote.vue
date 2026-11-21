<template>
  <figure class="plate">
    <p class="kicker">建议留下，调用另算</p>
    <div class="flow-split">
      <div class="node now">
        <strong>写下建议</strong>
        <span>推演仍赢不了，而且武装已经在封墙里面。<code>advise</code> 才是 <code>safemode</code>。<code>assessRun</code> 写入 <code>w8adv</code>，不调用。</span>
      </div>
      <div class="node later">
        <strong>键留着</strong>
        <span>威胁清空时删 <code>w8assess</code> 和 <code>w8roster</code>。<code>w8adv</code> 不删。没有别处再写或再删。<code>t</code> 是上次写下的拍。</span>
      </div>
      <div class="node stop">
        <strong>唯一调用</strong>
        <span>征服工人，且 <code>autoSafe</code> 为真。次数还在，当前没开，等级至少 2。缺省不设。平时的防御不走这里。</span>
      </div>
    </div>
    <figcaption>
      指挥官不打开安全模式，见 <a href="/mechanisms/commander">指挥官接管</a>。名单见 <a href="/mechanisms/defense">防御与威胁</a>。raid9 不调用，只读对方控制器上的 <code>safeMode</code>。
    </figcaption>
  </figure>
</template>

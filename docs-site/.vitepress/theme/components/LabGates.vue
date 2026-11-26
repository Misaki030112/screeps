<template>
  <figure class="plate">
    <p class="kicker">四个数，四道门</p>
    <div class="gates">
      <div class="node done">
        <strong>15000 · 现在不该再加码</strong>
        <span><code>ACT_HOME_STOR</code>。写进 <code>labReady.actOk</code>。存储能量低于它，缺口是 <code>homeStor</code>。已经装进输入实验室的原料继续反应。</span>
      </div>
      <div class="node now">
        <strong>5000 · 从存储取 boost 能量</strong>
        <span><code>STOR_SAFE</code>。能从存储计入的，只是高出这道线的部分。终端能量，以及实验室里已经有的能量，仍可以用来强化。产物到 60000 反应暂停。</span>
      </div>
      <div class="node">
        <strong>3000 · 终端里的工作库存</strong>
        <span>停放只挪终端里高出 3000 的钾和氧，再低不抽。KO 没有这道缓冲，整份离开终端。观察清单不对称：<code>kBuf</code> 只看终端的钾，<code>oBuf</code> 把终端和存储的氧加在一起。</span>
      </div>
      <div class="node">
        <strong>6000 · 终端要留的空位</strong>
        <span><code>TERM_FREE_TARGET</code>。1000 留给一次 KO 倒出，5000 留给下一次从 W47 来的钾。空位低于它，停放走紧的那一档。</span>
      </div>
    </div>
    <figcaption>
      整理终端时，家搬运工另读一道同为 15000 的地板。那道门在<a href="/mechanisms/haul">搬运页</a>，读的是 <code>reserveE</code>，键不在时按 15000。它和 <code>ACT_HOME_STOR</code> 是两个地方。
    </figcaption>
  </figure>
</template>

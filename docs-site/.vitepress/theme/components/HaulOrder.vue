<template>
  <figure class="plate">
    <p class="kicker">空手的家搬运工，先做完这些</p>
    <div class="arch-col">
      <div class="step">
        <span class="num">1</span>
        <div class="node now">
          <strong>矿物容器</strong>
          <span>手里已经拿着、并且标了这一趟的，送到终端或存储。防御地板以下，不再新开一趟。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">2</span>
        <div class="node">
          <strong>Boost</strong>
          <span>风筝兵在家等着时，先送 KO，再补实验室的能量。从存储取能量，取完须仍不少于 20000。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">3</span>
        <div class="node">
          <strong>终端紧</strong>
          <span>空位不够一次 1000 的倒出再加一次 5000 的钾。高出缓冲的氧、钾，以及 KO，放进存储。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">4</span>
        <div class="node">
          <strong>实验室日常</strong>
          <span>输入低于 1000 就灌，输出堆到 1000 就倒回终端。实验室旗标开着才有这一步。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">5</span>
        <div class="node">
          <strong>终端松</strong>
          <span>继续把多余的收到缓冲：氧、钾各留 3000。缓冲被用掉，再从存储补回。全程不搬能量。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">6</span>
        <div class="node now">
          <strong>外送到终端</strong>
          <span>RCL8 输能开着、存储至少 20000、这一趟至少 400：从存储搬进家的终端，留下不低于 18000。已经抱在身上的，排在第 1 步之前。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">7</span>
        <div class="node">
          <strong>还拿在手里的矿物</strong>
          <span>前面没接住的非能量送进存储。实验室开着时，第 4 步通常已经把它交给终端。</span>
        </div>
      </div>
    </div>
    <figcaption>
      这些步都在捡能量之前。第 3 到第 5 步要 <code>Memory.ops.labs</code> 已经给这间房配了反应。第 2 步看的是有没有风筝兵在家等，不看这个旗标。存储能量低于整理终端用的那条线时，第 3 步和第 5 步不新开；已经接在手上的会走完。第 6 步是 RCL8 才有的外送，条件和暂停写在正文。
    </figcaption>
  </figure>
</template>

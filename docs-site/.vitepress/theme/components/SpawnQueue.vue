<template>
  <figure class="plate">
    <p class="kicker">家的出生队列</p>
    <div class="arch">
      <div class="arch-col">
        <div class="step">
          <span class="num">1</span>
          <div class="node">
            <strong>紧急</strong>
            <span>没有活着的搬运工、女王、采集工或 filler。有矿工就按现有能量生小搬运工，否则生采集工。</span>
          </div>
        </div>
        <div class="step">
          <span class="num">2</span>
          <div class="node now">
            <strong>家里的守卫</strong>
            <span>满身体。付不清就占住队列。一只补能的都没有时，先补女王，让延伸继续灌。</span>
          </div>
        </div>
        <div class="step">
          <span class="num">3</span>
          <div class="node now">
            <strong>外矿防御</strong>
            <span>同样满身体。核心用近战，其余用远程。只有近满才按手里的能量来长。</span>
          </div>
        </div>
      </div>
      <div class="arch-col">
        <div class="step">
          <span class="num">4</span>
          <div class="node">
            <strong>矿工</strong>
            <span>按自己记住的走路时间提前生。上面的身体还欠着，这一步不开始。</span>
          </div>
        </div>
        <div class="step">
          <span class="num">5</span>
          <div class="node">
            <strong>后勤</strong>
            <span>女王、搬运工、外矿、filler、manager。升级工不在这一遍出生。</span>
          </div>
        </div>
        <div class="step">
          <span class="num">6</span>
          <div class="node">
            <strong>平民</strong>
            <span>升级工、建造、矿物矿工。排在后勤之后，也排在人已经点名的请求之后。</span>
          </div>
        </div>
      </div>
    </div>
    <figcaption>一座空闲出生点一拍只做第一件付得起的事。第二级或第三级还没付清时，矿工和平民都等。把身体改小，只留给紧急、外矿防御的近满，以及连续三百 tick 没有近满的那条恢复路径。</figcaption>
  </figure>
</template>

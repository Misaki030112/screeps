<template>
  <figure class="plate">
    <p class="kicker">先送源，再看枢纽</p>
    <div class="doors">
      <div>
        <p class="door-name">家 · 每 3 拍</p>
        <div class="arch-col">
          <div class="node now">
            <strong>源 link</strong>
            <span>30,11，以及后来立起、又不属于枢纽或控制器的那几座。至少 400，且不在冷却。有目标就送目标。这一拍没有目标，改送枢纽。</span>
          </div>
          <p class="arrow">先</p>
          <div class="node">
            <strong>枢纽 37,29</strong>
            <span>同样至少 400。只在目标还在时送出。没有目标就留着，不送给自己。</span>
          </div>
          <p class="arrow">后</p>
          <div class="node done">
            <strong>目标</strong>
            <span>允许升级，且控制器 link 30,31 低于 400。固定 filler 关着，没有第二接收端。</span>
          </div>
        </div>
      </div>
      <div>
        <p class="door-name">W47 · 每拍</p>
        <div class="arch-col">
          <div class="node now">
            <strong>源 A · 26,12</strong>
            <span>至少 50，控制器 link 还有空位，就送出较少的那一份。这一段不看 400。源 B 没有 link。</span>
          </div>
          <p class="arrow">先</p>
          <div class="node">
            <strong>枢纽 32,33</strong>
            <span>控制器 link 低于 400，枢纽至少 200，而且那边还有空位。冷却和源 A 各算各的。33,34 不送。</span>
          </div>
          <p class="arrow">后</p>
          <div class="node done">
            <strong>控制器 13,25</strong>
            <span>源 A 把它的空位用掉。枢纽只在它低于 400 时再补。</span>
          </div>
        </div>
      </div>
    </div>
    <figcaption>
      两边都是源先、枢纽后，同一拍里可以各送一次。家的源在没有目标时退回枢纽；家的枢纽没有这步退回。W47 的源 A 只要控制器还有空位就送，400 只约束枢纽。
    </figcaption>
  </figure>
</template>

<template>
  <figure class="plate">
    <p class="kicker">通向三级风筝兵</p>
    <ul class="legend">
      <li><i class="lg-done"></i>已经在代码里</li>
      <li><i class="lg-now"></i>现在卡在这里</li>
      <li><i class="lg-later"></i>计划中，还没有自动推进</li>
      <li><i class="lg-stop"></i>明确不做</li>
    </ul>
    <div class="phases">
      <div class="phase done">
        <div class="tag">已有</div>
        <div class="node done">
          <strong>家已到 RCL8，外矿、link、矿物线</strong>
          <span>家把多余能量送到 W47，不养只涨 GCL 的升级工。W47 把 K 送回家。KO 仍在家。</span>
        </div>
      </div>
      <div class="phase now">
        <div class="tag">现在</div>
        <div class="node now">
          <strong>能量垫</strong>
          <span>家的 15000 仍是防御垫。外送从 20000 起。W47 平时 2 只 15 WORK，第三只要存储连续 300 tick 不低于 30000。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">其后</div>
        <div class="node later">
          <strong>W47 拉到 RCL8</strong>
          <span>W47 还低于 8 级时，家才往这边送能量。到了 8 级，输能关掉，家的升级目标回到 1。不新开市场。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">其后</div>
        <div class="node later">
          <strong>工业缓冲，大约十万能量</strong>
          <span>实验室从能用的三座扩到六座、十座。缺的 H、X、Z、L、U 以后再决定。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">北极星</div>
        <div class="node later">
          <strong>一只完整的 T3 远程风筝兵</strong>
          <span>4 韧 / 28 远程 / 8 治疗 / 10 移动，加上拆家搭档。反应表里还没有这些化合物。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">不做</div>
        <div class="node stop">
          <strong>市场、主动开战、为了矿物再占外矿</strong>
          <span>代码里没有交易。袭击和征服模块默认关着。安全模式的 <code>autoSafe</code> 缺省不设。</span>
        </div>
      </div>
    </div>
    <figcaption>这是人的顺序，不是一个会自己跳阶段的状态机。能量政策以现在的代码为准，规划不反过来改它。</figcaption>
  </figure>
</template>

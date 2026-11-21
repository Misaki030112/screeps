<template>
  <figure class="plate">
    <p class="kicker">没武装，就只问这一次</p>
    <ul class="legend">
      <li><i class="lg-done"></i>没武装，原来的循环</li>
      <li><i class="lg-now"></i>点了名，这一拍被接住</li>
      <li><i class="lg-later"></i>交还角色，指令还留着</li>
    </ul>
    <div class="phases">
      <div class="phase done">
        <div class="tag">关</div>
        <div class="node done">
          <strong>Memory.cmd 不在，或 on 是假</strong>
          <span>一次判断。不调用后面的接管。角色、实验室旗标、软顶照旧。</span>
        </div>
      </div>
      <div class="phase now">
        <div class="tag">开</div>
        <div class="node now">
          <strong>只问袋子里活着的名字</strong>
          <span>c 是 creep 名，s 是建筑 id。塔、link、出生点在管理器里先问。creep 之前再看观察者、核弹、工厂、Power Spawn 和挂了指令的实验室。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">落</div>
        <div class="node later">
          <strong>接不住就交还</strong>
          <span>有 act 且接住了，逃跑和角色都不跑。职责做不了，或带了 fallback，这一拍回到角色。指令还在。</span>
        </div>
      </div>
    </div>
    <figcaption>
      缺省活 200 拍。sticky 不看时钟。整层开着时，到点就删。单条 on 为 0 的留下，但不执行。
    </figcaption>
  </figure>
</template>

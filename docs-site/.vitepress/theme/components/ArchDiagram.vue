<template>
  <figure class="plate">
    <p class="kicker">一个 tick 里谁先说话</p>
    <div class="arch-col">
      <div class="step">
        <span class="num">1</span>
        <div class="node">
          <strong>清掉死人</strong>
          <span>先碰一次 Memory.creeps，再删掉已经不在的名字。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">2</span>
        <div class="node">
          <strong>孵化</strong>
          <span>W47N8 的出生点进自己的队列。其余出生点进家的。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">3</span>
        <div>
          <p class="fork-label">已占领的房间在这里分开</p>
          <div class="doors">
            <div class="node now">
              <strong>W47N8</strong>
              <span>布局，然后 towerRun。towerRun 先 mark 本房和看得见的 W47N7，再 linkRun，再塔。然后离开这一支。</span>
            </div>
            <div class="node done">
              <strong>家，以及其他属于我们的房间</strong>
              <span>布局、塔、link、实验室、警报。外矿没有所有权，不进这里。</span>
            </div>
          </div>
        </div>
      </div>
      <div class="step">
        <span class="num">4</span>
        <div class="node">
          <strong>外矿，路，然后外矿警报</strong>
          <span>状态机先走完。家的控制器低于 6，道路直接返回。警报只补 CFG 里的两间矿。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">5</span>
        <div class="node">
          <strong>指挥官，开着才接管</strong>
          <span>没设 Memory.cmd 时，这里只是一次判断。袭击旗标在 creep 之前收一次。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">6</span>
        <div class="node now">
          <strong>Creep</strong>
          <span>先处理走不出去的格子。桶低于 2000，战斗和补能排到前面，其余可以停一拍。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">7</span>
        <div class="node done">
          <strong>收尾</strong>
          <span>换位锁上，再记账和统计。STATS 给人看，不指挥下一只 creep。</span>
        </div>
      </div>
    </div>
    <figcaption>
      顺序写在 src/main.js。W47 的模块只为 W47N8 跑，家的代码看不见它。
    </figcaption>
  </figure>
</template>

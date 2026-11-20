<template>
  <figure class="plate">
    <p class="kicker">家的墙，四段</p>
    <div class="states">
      <div class="node">
        <strong>off</strong>
        <span>还没到 6 级，或没有存储。墙还不插手升级。</span>
      </div>
      <div class="node">
        <strong>roads</strong>
        <span>路的阶段名还没到 done。升级停，能量去铺路。</span>
      </div>
      <div class="node">
        <strong>bank</strong>
        <span>路铺完了。存储未到 20000，或家里不平静。升级最多一只。</span>
      </div>
      <div class="node">
        <strong>build</strong>
        <span>已经记住开工。圈未合，或有效命中未到 10 万，升级再停。</span>
      </div>
    </div>
    <div class="doors">
      <div>
        <p class="door-name">升级让路</p>
        <ul class="stick">
          <li>
            <strong>roads · 目标 0</strong>
            <span>掉级时间低于 20000，留下一只按 700 长的。bank 不写这道 0，只把目标压到 1。</span>
          </li>
          <li>
            <strong>build · 圈和 10 万</strong>
            <span>圈还没合上，或最低一截有效命中还没到 100000，目标再写成 0。</span>
          </li>
          <li>
            <strong>终端、实验室、萃取器</strong>
            <span>这三种还有工地，同样写成 0。掉级保护仍然先于这道 0。</span>
          </li>
        </ul>
      </div>
      <div>
        <p class="door-name">从存储取，留下什么</p>
        <ul class="stick">
          <li>
            <strong>1300 · 外矿武装</strong>
            <span>threat.reserve。没有外矿处于武装，这一项是 0。</span>
          </li>
          <li>
            <strong>5000 · 6 级起的垫子</strong>
            <span>walls.FLOOR。塔的城门上限、城门的腐烂线是另外两个同值常数，正文各写各的。</span>
          </li>
          <li>
            <strong>15000 · 殖民地储备</strong>
            <span>reserveE。平常取存储要留在这三数里较大的那个之上。低于它，建造工不取。</span>
          </li>
        </ul>
      </div>
    </div>
    <figcaption>
      路的阶段名按顺序走：core、haul、W45N8、econ、home、swamp7、done。城墙平常要等到 done，并且存储不少于 20000、家里这一拍平静，才从 bank 记入 build。记入之后存储再跌，也不退回攒钱。紧急开工可以跳过铺路和攒钱。围城和基金开支可以把存储用到 5000 那一档，不必守着 15000。升级工的只数怎么被这些阶段改写，见升级页。
    </figcaption>
  </figure>
</template>

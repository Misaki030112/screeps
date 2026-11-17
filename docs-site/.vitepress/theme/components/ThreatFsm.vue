<template>
  <figure class="plate">
    <p class="kicker">外矿四态</p>
    <div class="states">
      <div class="node done">
        <strong>SAFE</strong>
        <span>没有要打的。外矿的人照常干活。</span>
      </div>
      <div class="node">
        <strong>THREAT</strong>
        <span>已经决定打。身体还在出生点里，或还在凑能量。</span>
      </div>
      <div class="node now">
        <strong>DEFEND</strong>
        <span>防御 creep 已经离站。清场之后回到 SAFE。</span>
      </div>
      <div class="node stop">
        <strong>WAIT</strong>
        <span>这一波等过去。看见空了，或时间到了，再回到 SAFE。</span>
      </div>
    </div>
    <div class="doors">
      <div>
        <p class="door-name">会打</p>
        <ul class="stick">
          <li>
            <strong>单人 Invader</strong>
            <span>没有治疗，远程不到 3，寿命至少 300。用风筝。</span>
          </li>
          <li>
            <strong>守卫</strong>
            <span>预定还在的房间里有战斗单位，或家里付得起满身体的升格波。</span>
          </li>
          <li>
            <strong>单独的核心</strong>
            <span>旁边没有战斗 Invader。用近战去拆，不用风筝。</span>
          </li>
        </ul>
      </div>
      <div>
        <p class="door-name">会等</p>
        <ul class="stick">
          <li>
            <strong>玩家</strong>
            <span>路线或家里出现玩家，等 1500 tick。不估打不打得过。</span>
          </li>
          <li>
            <strong>闸</strong>
            <span>没武装、桶低于 3000、这一天已经死过一只。</span>
          </li>
          <li>
            <strong>短寿命、升格、超时</strong>
            <span>寿命不够，或升格了又付不起满身体。准备或交战超时也等。一天四只不把已经判成要打的那几种送进等待；它只拦住再要的下一只，核心除外。</span>
          </li>
        </ul>
      </div>
    </div>
    <figcaption>
      纯决策在 <code>threat.step</code>。它只看这一拍的观察，不看游戏对象。W47N9 不进这台机器。
    </figcaption>
  </figure>
</template>

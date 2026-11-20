<template>
  <figure class="plate">
    <p class="kicker">三笔能量，各管一件事</p>
    <div class="flow-split">
      <div class="node">
        <strong>1300 · 武装时的垫子</strong>
        <span><code>threat.reserve</code>。有外矿处于武装时，建造取存储不要低于它，塔修城门也收到 5000。它不解除武装。队列守这 1300，只发生在已经 WAIT(gate)、又标着要灌能量的时候。</span>
      </div>
      <div class="node">
        <strong>15000 · 殖民地地板</strong>
        <span><code>Memory.defense.reserveE</code>。墙模块在键不在时当成 0。女王和搬运怎么读，写在<a href="/mechanisms/haul">搬运</a>；升级工怎么用这道地板，写在<a href="/mechanisms/upgrade">升级</a>。防御身体的第一只不改这道地板。</span>
      </div>
      <div class="node now">
        <strong>15000 / 25000 · 再加一只</strong>
        <span><code>extrasOk</code>。有存储时，家要 15000；出生点在 W47 且软顶开着时要 25000。只拦小队表还停在 1、又已经有一只的下一只。判成战斗波的不看这道门。</span>
      </div>
    </div>
    <figcaption>
      两处都写着 15000。一个是殖民地整天守着的地板，一个是「和平时再孵一只风筝」的门。1300 是第三件。第一只防御身体从延伸里出，三笔都不因此改写。
    </figcaption>
  </figure>
</template>

<template>
  <figure class="plate">
    <p class="kicker">桶低于 2000 时，谁先跑</p>
    <div class="phases">
      <div class="phase now">
        <div class="tag">0</div>
        <div class="node now">
          <strong>战斗，先跑，不停</strong>
          <span>guard、defender、w8defender、w8healer、w8guard、cqsquad、cqbreaker、cqatk、cqquad、raid9。这一批不停一拍。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">1</div>
        <div class="node">
          <strong>补能，接着跑，也不停</strong>
          <span>queen 和 w8filler。家里补延伸的是女王，W47 枢纽这一侧是 w8filler。角色名 filler 不在这张表里。</span>
        </div>
      </div>
      <div class="phase">
        <div class="tag">2</div>
        <div class="node later">
          <strong>其余。快到本拍上限就停一拍</strong>
          <span>表里没有的角色都是 2。已用 CPU 大于 tickLimit 减 5 时，这只 creep 剩下的意图整段跳过，包括寻路。</span>
        </div>
      </div>
    </div>
    <figcaption>
      桶不低于 2000，不排序，也不跳过。顺序就是 Game.creeps 的原顺序。同优先级仍按原来的先后。
    </figcaption>
  </figure>
</template>

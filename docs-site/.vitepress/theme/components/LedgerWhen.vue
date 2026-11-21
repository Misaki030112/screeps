<template>
  <figure class="plate">
    <p class="kicker">记账分在两处</p>
    <div class="phases">
      <div class="phase now">
        <div class="tag">开头</div>
        <div class="node now">
          <strong>裹进原来的方法</strong>
          <span>每个 global 一次。返回 OK 才加。失败不加。试算的孵化也不加。记账出错，原来的结果仍交回去。</span>
        </div>
      </div>
      <div class="phase done">
        <div class="tag">结尾</div>
        <div class="node done">
          <strong>换位之后记浪费</strong>
          <span>tick 只看能量源。再生前的最后一拍，把源里还剩的能量加进去，并把次数加 1。</span>
        </div>
      </div>
    </div>
    <figcaption>
      两笔都累加在 Memory.ledger。它们不挑选下一只 creep，也不是控制台每 10 拍的 STATS。
    </figcaption>
  </figure>
</template>

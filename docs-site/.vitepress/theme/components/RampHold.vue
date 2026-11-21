<template>
  <figure class="plate">
    <p class="kicker">每次只选出一座城门</p>
    <div class="arch-col">
      <div class="step">
        <span class="num">1</span>
        <div class="node">
          <strong>城门，或 34,30</strong>
          <span>还低于 10 万就选中。本地窗口开着也做。不比谁更破，按房间列出的先后。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">2</span>
        <div class="node now">
          <strong>软抬升</strong>
          <span>窗口关着，目标大于 0，存储不低于 0。更破的先往 10 万补。城门不进。实验室和工厂再高也不超过 30 万。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">3</span>
        <div class="node">
          <strong>比第一次看见的少过 1000</strong>
          <span>软抬升没选中时，按列出的顺序补第一座。窗口里也做。从 1 点补高的，这条碰不到。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">4</span>
        <div class="node">
          <strong>实验室和工厂补到 30 万</strong>
          <span>还差着的，更破的先补完。软抬升被跳过，或别人已经到了 10 万，这一步仍在。</span>
        </div>
      </div>
    </div>
    <figcaption>
      选出一座才修。塔里要高于 600，这一拍也不能在治疗或开枪。命中到了 10 万，只有 10 格以内的塔动手。
    </figcaption>
  </figure>
</template>

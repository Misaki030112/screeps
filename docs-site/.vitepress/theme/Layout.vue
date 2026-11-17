<script setup>
import DefaultTheme from 'vitepress/theme'

const { Layout } = DefaultTheme
</script>

<template>
  <Layout>
    <template #doc-after>
      <p class="colophon">
        机制以仓库 <code>src/</code> 为准，和 shard3 上正在跑的 <code>85c19c2e</code> 一致。会随 tick 变化的进度，只在「现状」里作为注明日期的快照。
      </p>
    </template>
  </Layout>
</template>

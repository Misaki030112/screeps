<script setup>
import DefaultTheme from 'vitepress/theme'

const { Layout } = DefaultTheme
</script>

<template>
  <Layout>
    <template #doc-after>
      <p class="colophon">
        机制以仓库 <code>src/</code> 为准，对照的提交是 <code>289a7f06</code>。会随 tick 变化的进度，只在「现状」里作为注明日期的快照。
      </p>
    </template>
  </Layout>
</template>

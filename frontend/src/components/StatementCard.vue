<template>
  <n-card
    :hoverable="!!onClick"
    size="small"
    :style="{ cursor: onClick ? 'pointer' : 'default' }"
    @click="onClick?.($event)"
  >
    <div class="card-header">
      <n-text strong>
        {{ statement.politician_name }}
        <n-text depth="3" style="font-weight: 400"> ({{ statement.party }})</n-text>
      </n-text>
      <n-tag
        :type="statusType"
        size="small"
        :bordered="false"
        round
      >
        {{ statusKey }}
      </n-tag>
    </div>

    <n-text depth="1" class="body-text">{{ statement.statement_text }}</n-text>

    <div class="meta">
      <n-text v-if="statement.category" depth="3" style="font-size: 11px;">
        {{ statement.category }}
      </n-text>

      <n-tooltip v-if="absoluteDate" trigger="hover">
        <template #trigger>
          <n-text depth="3" class="date-pill">{{ relativeTime }}</n-text>
        </template>
        {{ absoluteDate }}
      </n-tooltip>

      <n-button
        v-if="statement.source_url"
        tag="a"
        :href="statement.source_url"
        target="_blank"
        rel="noreferrer"
        text
        type="info"
        size="tiny"
        @click.stop
      >
        View Source
      </n-button>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NCard, NTag, NText, NTooltip } from 'naive-ui'
import type { StatementResponse, StatementStatus } from '@/api/types.gen'

const props = defineProps<{
  statement: StatementResponse
  onClick?: (e: MouseEvent) => void
}>()

const STATUS_TYPE_MAP: Record<StatementStatus, 'success' | 'warning' | 'error' | 'default'> = {
  verified: 'success',
  pending: 'warning',
  disputed: 'error',
  retracted: 'default',
}

const statusKey = computed<StatementStatus>(() => props.statement.status ?? 'retracted')
const statusType = computed(() => STATUS_TYPE_MAP[statusKey.value])

const absoluteDate = computed(() =>
  props.statement.statement_date
    ? new Date(props.statement.statement_date).toLocaleDateString('en-CA')
    : ''
)

const relativeTime = computed(() =>
  props.statement.statement_date ? getRelativeTime(props.statement.statement_date) : ''
)

function getRelativeTime(iso: string): string {
  const then = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - then.getTime()

  const mins = Math.floor(diffMs / 60000)
  if (mins < 60) return `${mins} minute${mins !== 1 ? 's' : ''} ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} hour${hrs !== 1 ? 's' : ''} ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days} day${days !== 1 ? 's' : ''} ago`

  // Calendar-accurate year/month diff
  let years = now.getFullYear() - then.getFullYear()
  let months = now.getMonth() - then.getMonth()
  if (now.getDate() < then.getDate()) months -= 1
  if (months < 0) {
    years -= 1
    months += 12
  }

  if (years < 1) {
    if (months < 1) return `${days} day${days !== 1 ? 's' : ''} ago`
    return `${months} month${months !== 1 ? 's' : ''} ago`
  }
  const yPart = `${years} year${years !== 1 ? 's' : ''}`
  const mPart = months > 0 ? ` ${months} month${months !== 1 ? 's' : ''}` : ''
  return `${yPart}${mPart} ago`
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
}

.body-text {
  display: block;
  font-size: 13px;
  line-height: 1.55;
  margin-bottom: 10px;
}

.meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: center;
  font-size: 11px;
}

.date-pill {
  font-size: 11px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.25);
  cursor: default;
}
</style>

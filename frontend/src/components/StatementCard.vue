<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { StatementResponse, StatementStatus } from '@/api/types.gen'

const props = defineProps<{
  statement: StatementResponse
}>()

defineEmits<{
  (e: 'click', statement: StatementResponse): void
}>()

const attrs = useAttrs()
const isClickable = computed(() => typeof attrs.onClick === 'function')

const statusKey = computed<StatementStatus>(() => props.statement.status ?? 'retracted')

const dateStr = computed(() =>
  props.statement.statement_date
    ? new Date(props.statement.statement_date).toLocaleDateString('en-CA')
    : ''
)

const relativeTime = computed(() =>
  props.statement.statement_date ? getRelativeTime(props.statement.statement_date) : ''
)

function getRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} minute${mins !== 1 ? 's' : ''} ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} hour${hrs !== 1 ? 's' : ''} ago`
  const days = Math.floor(hrs / 24)
  return `${days} day${days !== 1 ? 's' : ''} ago`
}
</script>

<template>
  <article class="statement-card" :class="{ 'is-clickable': isClickable }">
    <header class="statement-card__header">
      <span class="statement-card__title">
        {{ statement.politician_name }}
        <span class="statement-card__party">({{ statement.party }})</span>
      </span>
      <span class="status-tag" :class="`status-tag--${statusKey}`">
        {{ statusKey }}
      </span>
    </header>

    <p class="statement-card__body">{{ statement.statement_text }}</p>

    <div class="statement-card__meta">
      <span v-if="statement.category">{{ statement.category }}</span>
      <span v-if="dateStr" class="date-pill" :data-tooltip="dateStr">
        {{ relativeTime }}
      </span>
      <a
        v-if="statement.source_url"
        :href="statement.source_url"
        target="_blank"
        rel="noreferrer"
        class="statement-card__source"
        @click.stop
      >
        <span aria-hidden="true" class="statement-card__source-glyph">↗</span>
        View Source
      </a>
    </div>
  </article>
</template>

<style scoped>
.statement-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 14px var(--space-4);
  font-family: var(--font-sans);
  transition: border-color 0.15s;
}

.statement-card:hover {
  border-color: var(--color-border-hover);
}

.statement-card.is-clickable {
  cursor: pointer;
}

.statement-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.statement-card__title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-1);
}

.statement-card__party {
  font-weight: var(--font-normal);
  color: var(--color-text-2);
}

.statement-card__body {
  font-size: var(--text-base);
  color: var(--color-text-1);
  line-height: var(--leading-normal);
  margin: 0 0 10px 0;
}

.statement-card__meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--color-text-3);
}

.statement-card__source {
  color: var(--color-info);
  text-decoration: none;
  font-size: var(--text-xs);
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.statement-card__source:hover {
  color: var(--color-info-hover);
}

.statement-card__source-glyph {
  font-size: var(--text-sm);
  line-height: 1;
}

/* Status tag — pill with muted background and solid foreground */
.status-tag {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-full);
  font-size: var(--text-2xs);
  font-weight: var(--font-medium);
  padding: 2px var(--space-2);
  text-transform: lowercase;
}

.status-tag--verified {
  background: var(--color-success-muted);
  color: var(--color-success);
}

.status-tag--pending {
  background: var(--color-warning-muted);
  color: var(--color-warning);
}

.status-tag--disputed {
  background: var(--color-error-muted);
  color: var(--color-error);
}

.status-tag--retracted {
  background: var(--color-status-retracted-bg);
  color: var(--color-status-retracted-fg);
}

/* Date pill — dashed underline with absolute-date tooltip on hover */
.date-pill {
  position: relative;
  cursor: default;
  border-bottom: 1px dashed var(--color-border-dashed);
}

.date-pill::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-4px);
  background: var(--color-bg-popover);
  border: 1px solid var(--color-border-popover);
  border-radius: var(--radius-md);
  padding: var(--space-1) var(--space-2);
  white-space: nowrap;
  font-size: var(--text-2xs);
  color: var(--color-text-popover);
  box-shadow: var(--shadow-popover);
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.1s;
  z-index: 10;
}

.date-pill:hover::after {
  opacity: 1;
  visibility: visible;
}
</style>

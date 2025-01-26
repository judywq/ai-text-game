import { type ColumnDef } from '@tanstack/vue-table'
import { h } from 'vue'
import type { EssayRequest } from '@/types/essay'

const MAX_CHARS = 50

export const columns: ColumnDef<EssayRequest>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'essay',
    header: 'Essay',
    cell: ({ row }) => {
      const essay = row.getValue('essay') as string
      return h(
        'div',
        { class: 'max-w-[300px] truncate' },
        essay.substring(0, MAX_CHARS) + (essay.length > MAX_CHARS ? '...' : ''),
      )
    },
  },
  {
    accessorKey: 'score',
    header: 'Score',
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => {
      const status = row.getValue('status') as string
      return h(
        'div',
        {
          class: {
            'text-green-600': status === 'COMPLETED',
            'text-red-600': status === 'FAILED',
            'text-yellow-600': status === 'PENDING',
          },
        },
        status,
      )
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Created At',
    cell: ({ row }) => {
      return new Date(row.getValue('created_at')).toLocaleString()
    },
    sortingFn: 'datetime',
  },
]

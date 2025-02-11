import { type ColumnDef } from '@tanstack/vue-table'
import { h } from 'vue'
import type { GameStory } from '@/types/game'

export const columns: ColumnDef<GameStory>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'title',
    header: 'Title',
    cell: ({ row }) => {
      const title = row.getValue('title') as string
      return h(
        'div',
        { class: 'max-w-[300px] truncate' },
        title
      )
    },
  },
  {
    accessorKey: 'genre',
    header: 'Genre',
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
            'text-red-600': status === 'ABANDONED',
            'text-yellow-600': status === 'IN_PROGRESS',
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

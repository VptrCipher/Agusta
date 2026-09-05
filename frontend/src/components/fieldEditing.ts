import type {EditableFieldConfig, EditableFieldType} from '../types/records'

interface EditableFieldTypeDefinition {
  emptyValue: unknown
  normalizeForDraft: (value: unknown) => unknown
  normalizeForSave: (value: unknown) => unknown
  isEqual: (left: unknown, right: unknown) => boolean
}

const stringValue = (value: unknown) => value === null || value === undefined ? '' : String(value)

const nullableStringValue = (value: unknown) => {
  const next = stringValue(value)
  return next || null
}

const stringArrayValue = (value: unknown) => Array.isArray(value) ? value.map((item) => String(item)) : []

const normalizedStringArray = (value: unknown) => stringArrayValue(value).toSorted()

const booleanValue = (value: unknown) => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') return value.toLowerCase() === 'true'
  return Boolean(value)
}

const numberValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return null
  const next = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(next) ? next : null
}

const dateTimeValue = (value: unknown) => {
  if (!value) return null
  const parsed = new Date(String(value))
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString()
}

const scalarStringDefinition: EditableFieldTypeDefinition = {
  emptyValue: '',
  normalizeForDraft: stringValue,
  normalizeForSave: stringValue,
  isEqual: (left, right) => stringValue(left) === stringValue(right),
}

const nullableStringDefinition: EditableFieldTypeDefinition = {
  emptyValue: null,
  normalizeForDraft: nullableStringValue,
  normalizeForSave: nullableStringValue,
  isEqual: (left, right) => nullableStringValue(left) === nullableStringValue(right),
}

export const editableFieldRegistry: Record<EditableFieldType, EditableFieldTypeDefinition> = {
  text: scalarStringDefinition,
  textarea: scalarStringDefinition,
  markdown: scalarStringDefinition,
  datetime: {
    emptyValue: null,
    normalizeForDraft: dateTimeValue,
    normalizeForSave: dateTimeValue,
    isEqual: (left, right) => dateTimeValue(left) === dateTimeValue(right),
  },
  select: nullableStringDefinition,
  multiSelect: {
    emptyValue: [],
    normalizeForDraft: stringArrayValue,
    normalizeForSave: stringArrayValue,
    isEqual: (left, right) => {
      const normalizedLeft = normalizedStringArray(left)
      const normalizedRight = normalizedStringArray(right)
      return normalizedLeft.length === normalizedRight.length
        && normalizedLeft.every((item, index) => item === normalizedRight[index])
    },
  },
  tags: {
    emptyValue: [],
    normalizeForDraft: stringArrayValue,
    normalizeForSave: stringArrayValue,
    isEqual: (left, right) => {
      const normalizedLeft = normalizedStringArray(left)
      const normalizedRight = normalizedStringArray(right)
      return normalizedLeft.length === normalizedRight.length
        && normalizedLeft.every((item, index) => item === normalizedRight[index])
    },
  },
  user: nullableStringDefinition,
  number: {
    emptyValue: null,
    normalizeForDraft: numberValue,
    normalizeForSave: numberValue,
    isEqual: (left, right) => numberValue(left) === numberValue(right),
  },
  boolean: {
    emptyValue: false,
    normalizeForDraft: booleanValue,
    normalizeForSave: booleanValue,
    isEqual: (left, right) => booleanValue(left) === booleanValue(right),
  },
}

export function editableFieldDefinition(field: EditableFieldConfig) {
  return editableFieldRegistry[field.type || 'text']
}

export function editableFieldEmptyValue(field: EditableFieldConfig) {
  if (Object.hasOwn(field, 'emptyValue')) return field.emptyValue
  return editableFieldDefinition(field).emptyValue
}

export function normalizeEditableDraftValue(field: EditableFieldConfig, value: unknown) {
  const source = value === null || value === undefined ? editableFieldEmptyValue(field) : value
  return editableFieldDefinition(field).normalizeForDraft(source)
}

export function normalizeEditableSaveValue(field: EditableFieldConfig, value: unknown) {
  return editableFieldDefinition(field).normalizeForSave(value)
}

export function editableValuesEqual(field: EditableFieldConfig, left: unknown, right: unknown) {
  return editableFieldDefinition(field).isEqual(left, right)
}

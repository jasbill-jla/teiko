import { describe, expect, it } from 'vitest'
import { toCsv } from './csv'

describe('toCsv', () => {
  it('joins columns and rows with commas, using CRLF line endings', () => {
    const csv = toCsv(
      ['Project', 'Age'],
      [
        ['prj1', 42],
        ['prj2', 7],
      ],
    )

    expect(csv).toBe('Project,Age\r\nprj1,42\r\nprj2,7')
  })

  it('renders null fields as empty', () => {
    const csv = toCsv(['Condition'], [[null]])

    expect(csv).toBe('Condition\r\n')
  })

  it('quotes and escapes fields containing commas, quotes, or newlines', () => {
    const csv = toCsv(['Note'], [['a,b'], ['say "hi"'], ['line1\nline2']])

    expect(csv).toBe('Note\r\n"a,b"\r\n"say ""hi"""\r\n"line1\nline2"')
  })

  it('leaves plain fields unquoted', () => {
    const csv = toCsv(['Sample Type'], [['PBMC']])

    expect(csv).toBe('Sample Type\r\nPBMC')
  })
})

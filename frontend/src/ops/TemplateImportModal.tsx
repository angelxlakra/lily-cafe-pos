/**
 * TemplateImportModal (ops look)
 *
 * One-time setup: paste the WhatsApp stock checklist, check what was read
 * from it, then create the categories and items. Anything that fails is
 * named afterwards and can be retried.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../api/inventory';
import { useDialogFocus } from '../hooks/useDialogFocus';
import { describeApiError } from '../utils/apiError';
import { formatQty } from '../utils/countQuantity';
import { parseWhatsAppTemplate, type ParsedItem } from '../utils/unitParser';
import type { InventoryCategory } from '../types/inventory';

interface TemplateImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingCategories: InventoryCategory[];
}

type ImportStep = 'input' | 'preview' | 'importing' | 'complete';
type Failure = { item: ParsedItem; reason: string };

export default function TemplateImportModal({
  isOpen,
  onClose,
  existingCategories,
}: TemplateImportModalProps) {
  const queryClient = useQueryClient();
  const dialogRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);

  const [step, setStep] = useState<ImportStep>('input');
  const [templateText, setTemplateText] = useState('');
  const [parsedItems, setParsedItems] = useState<ParsedItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<{
    categoriesCreated: number;
    itemsCreated: number;
    failures: Failure[];
    categoriesFailed: string[];
  } | null>(null);

  const handleClose = () => {
    setStep('input');
    setTemplateText('');
    setParsedItems([]);
    setError(null);
    setResult(null);
    setProgress(0);
    onClose();
  };

  // Escape, focus trap and focus restore. Not while items are being created.
  useDialogFocus(dialogRef, handleClose, step === 'importing');
  // Move focus into the dialog without opening the phone keyboard: the
  // heading, not the textarea.
  useEffect(() => {
    if (isOpen) headingRef.current?.focus();
  }, [isOpen]);

  const handleParse = () => {
    setError(null);
    if (!templateText.trim()) {
      setError('Paste the checklist text first.');
      return;
    }
    try {
      const items = parseWhatsAppTemplate(templateText);
      if (items.length === 0) {
        setError("Couldn't find any items in that text. Check that each line has a name and a number.");
        return;
      }
      setParsedItems(items);
      setStep('preview');
    } catch (parseError) {
      setError(`Couldn't read that text. ${(parseError as Error).message}`);
    }
  };

  const importMutation = useMutation({
    mutationFn: async (items: ParsedItem[]) => {
      const categoryIds = new Map<string, number>(
        existingCategories.map(category => [category.name.toLowerCase(), category.id]),
      );
      const categoriesFailed: string[] = [];
      let categoriesCreated = 0;

      for (const name of [...new Set(items.map(item => item.category))]) {
        if (categoryIds.has(name.toLowerCase())) continue;
        try {
          const created = await inventoryApi.createCategory({ name });
          categoryIds.set(name.toLowerCase(), created.id);
          categoriesCreated++;
        } catch {
          // The items still get created, just without a category.
          categoriesFailed.push(name);
        }
      }

      const failures: Failure[] = [];
      let itemsCreated = 0;
      for (const [index, item] of items.entries()) {
        setProgress(index + 1);
        try {
          await inventoryApi.createItem({
            name: item.name,
            unit: item.unit,
            current_quantity: item.quantity,
            min_threshold: item.minThreshold,
            category_id: categoryIds.get(item.category.toLowerCase()),
            cost_per_unit: undefined,
          });
          itemsCreated++;
        } catch (itemError) {
          failures.push({ item, reason: describeApiError(itemError) });
        }
      }

      return { categoriesCreated, itemsCreated, failures, categoriesFailed };
    },
    onSuccess: summary => {
      setResult(previous => ({
        categoriesCreated: (previous?.categoriesCreated ?? 0) + summary.categoriesCreated,
        itemsCreated: (previous?.itemsCreated ?? 0) + summary.itemsCreated,
        failures: summary.failures,
        categoriesFailed: summary.categoriesFailed,
      }));
      setStep('complete');
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
    onError: importError => {
      setError(`The import stopped. ${describeApiError(importError)}`);
      setStep('preview');
    },
  });

  const startImport = (items: ParsedItem[]) => {
    setProgress(0);
    setStep('importing');
    importMutation.mutate(items);
  };

  // Preview grouped by category: the same shape the count will have.
  const groups = useMemo(() => {
    const byCategory = new Map<string, ParsedItem[]>();
    parsedItems.forEach(item => {
      byCategory.set(item.category, [...(byCategory.get(item.category) ?? []), item]);
    });
    return [...byCategory.entries()];
  }, [parsedItems]);

  if (!isOpen) return null;

  const importingCount = importMutation.variables?.length ?? parsedItems.length;

  return (
    <div className="count-sheet-wrap">
      <div className="count-scrim" onClick={step === 'importing' ? undefined : handleClose} />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-title"
        className="count-sheet wide"
      >
        <div className="count-sheet-body">
          <h2 id="import-title" ref={headingRef} tabIndex={-1} style={{ outline: 'none' }}>
            Import your checklist
          </h2>
          <p className="muted">Paste the WhatsApp stock list to create all its items at once.</p>

          {error && <div role="alert" className="count-fail">{error}</div>}

          {step === 'input' && (
            <>
              <div className="ops-form full" style={{ marginTop: 12 }}>
                <label>
                  Checklist text
                  <textarea
                    value={templateText}
                    onChange={event => setTemplateText(event.target.value)}
                    placeholder={'_#DRY GROCERY#_\nRAMEN NOODLES : 46\nSALT : 0\nBREAD CRUMB : ½'}
                  />
                </label>
              </div>
              <h3>What the app can read</h3>
              <ul className="su-read">
                <li>Category lines: <code>*DRY GROCERY*</code> or <code>_#DRY GROCERY#_</code></li>
                <li>Item lines: <code>SALT : 2</code> or <code>SALT 2</code></li>
                <li>Halves and quarters: ½, ¼, ¾</li>
                <li>Weights and volumes: 50g, 4kg, 500ml, 1L</li>
                <li>YES becomes 1, NO becomes 0</li>
              </ul>
            </>
          )}

          {step === 'preview' && (
            <>
              <p className="count-totals">
                Read <strong>{parsedItems.length} item{parsedItems.length === 1 ? '' : 's'}</strong> in{' '}
                <strong>{groups.length} categor{groups.length === 1 ? 'y' : 'ies'}</strong>. Check a few, then add them.
              </p>

              {groups.map(([category, items]) => (
                <section key={category} aria-labelledby={`preview-${category}`}>
                  <h3 id={`preview-${category}`}>
                    <span>{category}</span>
                    <span className="muted">{items.length}</span>
                  </h3>
                  <ul className="count-list">
                    {items.map((item, index) => (
                      <li key={`${item.name}-${index}`} className="su-rows">
                        <span style={{ minWidth: 0, overflowWrap: 'anywhere' }}>{item.name}</span>
                        <span className="qty">
                          {formatQty(item.quantity)} <span className="muted">{item.unit}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </>
          )}

          {step === 'importing' && (
            <div className="su-done">
              <p aria-live="polite"><strong>Adding item {progress} of {importingCount}</strong></p>
              <div
                className="su-prog"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={importingCount}
                aria-valuenow={progress}
                aria-label="Items added"
              >
                <div style={{ transform: `scaleX(${importingCount ? progress / importingCount : 0})` }} />
              </div>
              <p className="muted">Keep this window open until it finishes.</p>
            </div>
          )}

          {step === 'complete' && result && (
            <>
              <div className="su-done">
                <h3 style={{ display: 'block', fontSize: 20 }}>
                  {result.failures.length === 0 ? 'All imported' : 'Imported, with some left out'}
                </h3>
                <p>
                  {result.itemsCreated} item{result.itemsCreated === 1 ? '' : 's'} and{' '}
                  {result.categoriesCreated} categor{result.categoriesCreated === 1 ? 'y' : 'ies'} added
                  {result.failures.length > 0 && <> · {result.failures.length} not added</>}
                </p>
              </div>

              {result.categoriesFailed.length > 0 && (
                <p className="muted">
                  These categories couldn't be created, so their items went in without one:{' '}
                  <strong>{result.categoriesFailed.join(', ')}</strong>. You can add them
                  under Categories and move the items across.
                </p>
              )}

              {result.failures.length > 0 && (
                <section aria-labelledby="import-failures">
                  <h3 id="import-failures" className="warn">Not added</h3>
                  <ul className="count-list">
                    {result.failures.map(({ item, reason }, index) => (
                      <li key={`${item.name}-${index}`} style={{ padding: '8px 12px' }}>
                        <strong style={{ overflowWrap: 'anywhere' }}>{item.name}</strong>
                        <div className="muted">{reason}</div>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </div>

        <div className="count-actions">
          {step === 'input' && (
            <>
              <button type="button" onClick={handleClose} className="btn ghost">Cancel</button>
              <button type="button" onClick={handleParse} className="btn">Check the list</button>
            </>
          )}

          {step === 'preview' && (
            <>
              <button type="button" onClick={() => setStep('input')} className="btn ghost">Back to the text</button>
              <button type="button" onClick={() => startImport(parsedItems)} className="btn">
                Add {parsedItems.length} item{parsedItems.length === 1 ? '' : 's'}
              </button>
            </>
          )}

          {step === 'complete' && result && (
            <>
              {result.failures.length > 0 ? (
                <button type="button" onClick={() => startImport(result.failures.map(failure => failure.item))} className="btn ghost">
                  {result.failures.length === 1 ? 'Try that one again' : `Try those ${result.failures.length} again`}
                </button>
              ) : (
                <button type="button" onClick={() => { setStep('input'); setTemplateText(''); setParsedItems([]); }} className="btn ghost">
                  Import another list
                </button>
              )}
              <button type="button" onClick={handleClose} className="btn">Done</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

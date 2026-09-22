/**
 * TemplateImportModal
 *
 * One-time setup: paste the WhatsApp stock checklist, check what was read
 * from it, then create the categories and items. Anything that fails is
 * named afterwards and can be retried.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { X, Upload, CheckCircle, Warning } from '@phosphor-icons/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../../api/inventory';
import { useDialogFocus } from '../../hooks/useDialogFocus';
import { describeApiError } from '../../utils/apiError';
import { formatQty } from '../../utils/countQuantity';
import { parseWhatsAppTemplate, type ParsedItem } from '../../utils/unitParser';
import type { InventoryCategory } from '../../types/inventory';

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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-title"
        className="bg-off-white rounded-xl shadow-strong max-w-2xl w-full flex flex-col max-h-[90dvh] animate-scale-in"
      >
        <div className="flex items-start justify-between gap-3 p-4 md:p-6 border-b border-neutral-border shrink-0">
          <div>
            <h2 id="import-title" ref={headingRef} tabIndex={-1} className="font-heading text-2xl! text-neutral-text-dark focus:outline-none">
              Import your checklist
            </h2>
            <p className="text-sm text-neutral-text-muted mt-1">
              Paste the WhatsApp stock list to create all its items at once.
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={step === 'importing'}
            aria-label="Close"
            className="size-12 -mr-2 -mt-2 shrink-0 grid place-items-center rounded-lg text-neutral-text-muted hover:text-neutral-text-dark hover:bg-cream/60 disabled:opacity-40"
          >
            <X size={22} aria-hidden />
          </button>
        </div>

        <div className="p-4 md:p-6 overflow-y-auto flex-1">
          {error && (
            <div role="alert" className="mb-4 p-3 rounded-lg border border-error/40 bg-error/5 flex items-start gap-2">
              <Warning size={18} className="text-error shrink-0 mt-0.5" weight="fill" aria-hidden />
              <p className="text-sm text-neutral-text-body">{error}</p>
            </div>
          )}

          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="template-text" className="block text-sm font-medium text-neutral-text-body mb-2">
                  Checklist text
                </label>
                <textarea
                  id="template-text"
                  value={templateText}
                  onChange={event => setTemplateText(event.target.value)}
                  placeholder={'_#DRY GROCERY#_\nRAMEN NOODLES : 46\nSALT : 0\nBREAD CRUMB : ½'}
                  className="input-field w-full h-56 md:h-72 font-mono text-sm"
                />
              </div>

              <div className="rounded-lg border border-neutral-border bg-cream/40 p-4">
                <h3 className="subheading text-neutral-text-dark mb-2">What the app can read</h3>
                <ul className="text-sm text-neutral-text-body space-y-1">
                  <li>Category lines: <code>*DRY GROCERY*</code> or <code>_#DRY GROCERY#_</code></li>
                  <li>Item lines: <code>SALT : 2</code> or <code>SALT 2</code></li>
                  <li>Halves and quarters: ½, ¼, ¾</li>
                  <li>Weights and volumes: 50g, 4kg, 500ml, 1L</li>
                  <li>YES becomes 1, NO becomes 0</li>
                </ul>
              </div>
            </div>
          )}

          {step === 'preview' && (
            <div className="space-y-4">
              <p className="text-neutral-text-body tabular-nums">
                Read <strong className="text-neutral-text-dark">{parsedItems.length} item{parsedItems.length === 1 ? '' : 's'}</strong> in{' '}
                <strong className="text-neutral-text-dark">{groups.length} categor{groups.length === 1 ? 'y' : 'ies'}</strong>. Check a few, then add them.
              </p>

              {groups.map(([category, items]) => (
                <section key={category} aria-labelledby={`preview-${category}`}>
                  <h3 id={`preview-${category}`} className="subheading text-neutral-text-dark mb-1 flex items-baseline justify-between gap-2">
                    <span className="truncate">{category}</span>
                    <span className="shrink-0 font-normal text-neutral-text-muted tabular-nums">{items.length}</span>
                  </h3>
                  <ul className="card divide-y divide-neutral-border overflow-hidden">
                    {items.map((item, index) => (
                      <li key={`${item.name}-${index}`} className="flex items-center justify-between gap-3 px-3 py-2">
                        <span className="min-w-0 break-words text-neutral-text-dark">{item.name}</span>
                        <span className="shrink-0 tabular-nums text-neutral-text-body">
                          {formatQty(item.quantity)} <span className="text-neutral-text-muted">{item.unit}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          )}

          {step === 'importing' && (
            <div className="py-10 text-center">
              <p className="text-lg font-medium text-neutral-text-dark tabular-nums" aria-live="polite">
                Adding item {progress} of {importingCount}
              </p>
              <div
                className="mx-auto mt-4 h-1.5 w-full max-w-sm rounded-full bg-neutral-border/60 overflow-hidden"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={importingCount}
                aria-valuenow={progress}
                aria-label="Items added"
              >
                <div
                  className="h-full origin-left bg-lily-green-deep transition-transform duration-300 ease-(--ease-settle)"
                  style={{ transform: `scaleX(${importingCount ? progress / importingCount : 0})` }}
                />
              </div>
              <p className="text-sm text-neutral-text-muted mt-3">Keep this window open until it finishes.</p>
            </div>
          )}

          {step === 'complete' && result && (
            <div className="space-y-5">
              <div className="text-center py-4">
                {result.failures.length === 0 ? (
                  <>
                    <CheckCircle size={56} weight="fill" className="mx-auto text-lily-ink" aria-hidden />
                    <h3 className="font-heading text-2xl! text-neutral-text-dark mt-3">All imported</h3>
                  </>
                ) : (
                  <>
                    <Warning size={56} weight="fill" className="mx-auto text-warning" aria-hidden />
                    <h3 className="font-heading text-2xl! text-neutral-text-dark mt-3">Imported, with some left out</h3>
                  </>
                )}
                <p className="text-neutral-text-body mt-2 tabular-nums">
                  {result.itemsCreated} item{result.itemsCreated === 1 ? '' : 's'} and{' '}
                  {result.categoriesCreated} categor{result.categoriesCreated === 1 ? 'y' : 'ies'} added
                  {result.failures.length > 0 && <> · {result.failures.length} not added</>}
                </p>
              </div>

              {result.categoriesFailed.length > 0 && (
                <p className="text-sm text-neutral-text-body">
                  These categories couldn't be created, so their items went in without one:{' '}
                  <strong className="text-neutral-text-dark">{result.categoriesFailed.join(', ')}</strong>. You can add them
                  in the Categories tab and move the items across.
                </p>
              )}

              {result.failures.length > 0 && (
                <section aria-labelledby="import-failures">
                  <h3 id="import-failures" className="subheading text-neutral-text-dark mb-1">Not added</h3>
                  <ul className="card divide-y divide-neutral-border overflow-hidden">
                    {result.failures.map(({ item, reason }, index) => (
                      <li key={`${item.name}-${index}`} className="px-3 py-2">
                        <div className="font-medium text-neutral-text-dark break-words">{item.name}</div>
                        <div className="text-sm text-neutral-text-body">{reason}</div>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 p-4 md:p-6 border-t border-neutral-border shrink-0">
          {step === 'input' && (
            <>
              <button onClick={handleClose} className="btn-ghost">Cancel</button>
              <button onClick={handleParse} className="btn-primary">Check the list</button>
            </>
          )}

          {step === 'preview' && (
            <>
              <button onClick={() => setStep('input')} className="btn-ghost">Back to the text</button>
              <button
                onClick={() => startImport(parsedItems)}
                className="btn-primary inline-flex items-center gap-2"
              >
                <Upload size={20} weight="fill" aria-hidden />
                Add {parsedItems.length} item{parsedItems.length === 1 ? '' : 's'}
              </button>
            </>
          )}

          {step === 'complete' && result && (
            <>
              {result.failures.length > 0 ? (
                <button
                  onClick={() => startImport(result.failures.map(failure => failure.item))}
                  className="btn-secondary"
                >
                  {result.failures.length === 1 ? 'Try that one again' : `Try those ${result.failures.length} again`}
                </button>
              ) : (
                <button onClick={() => { setStep('input'); setTemplateText(''); setParsedItems([]); }} className="btn-ghost">
                  Import another list
                </button>
              )}
              <button onClick={handleClose} className="btn-primary">Done</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * TemplateImportModal Component
 *
 * One-time setup tool to import inventory items from WhatsApp template.
 * Parses mixed formats (fractions, YES/NO, weights) and bulk creates items.
 */

import { useState } from 'react';
import { X, Upload, CheckCircle, Warning } from '@phosphor-icons/react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../../api/inventory';
import { parseWhatsAppTemplate, type ParsedItem } from '../../utils/unitParser';
import type { InventoryCategory } from '../../types/inventory';

interface TemplateImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingCategories: InventoryCategory[];
}

type ImportStep = 'input' | 'preview' | 'importing' | 'complete';

export default function TemplateImportModal({
  isOpen,
  onClose,
  existingCategories
}: TemplateImportModalProps) {
  const queryClient = useQueryClient();

  const [step, setStep] = useState<ImportStep>('input');
  const [templateText, setTemplateText] = useState('');
  const [parsedItems, setParsedItems] = useState<ParsedItem[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [importResults, setImportResults] = useState<{
    categoriesCreated: number;
    itemsCreated: number;
    itemsFailed: number;
  }>({ categoriesCreated: 0, itemsCreated: 0, itemsFailed: 0 });

  const handleParse = () => {
    setErrors([]);

    if (!templateText.trim()) {
      setErrors(['Please paste your WhatsApp template text']);
      return;
    }

    try {
      const items = parseWhatsAppTemplate(templateText);

      if (items.length === 0) {
        setErrors(['No items found in the template. Please check the format.']);
        return;
      }

      setParsedItems(items);
      setStep('preview');
    } catch (error: any) {
      setErrors([`Parsing error: ${error.message}`]);
    }
  };

  const importMutation = useMutation({
    mutationFn: async () => {
      const categoryMap = new Map<string, number>();
      let categoriesCreated = 0;
      let itemsCreated = 0;
      let itemsFailed = 0;

      // First, create missing categories
      const uniqueCategories = [...new Set(parsedItems.map(item => item.category))];

      // Map existing categories
      existingCategories.forEach(cat => {
        categoryMap.set(cat.name.toLowerCase(), cat.id);
      });

      // Create new categories
      for (const categoryName of uniqueCategories) {
        const lowerName = categoryName.toLowerCase();

        if (!categoryMap.has(lowerName)) {
          try {
            const newCategory = await inventoryApi.createCategory({ name: categoryName });
            categoryMap.set(lowerName, newCategory.id);
            categoriesCreated++;
          } catch (error) {
            console.error(`Failed to create category ${categoryName}:`, error);
          }
        }
      }

      // Create items
      for (const item of parsedItems) {
        try {
          const categoryId = categoryMap.get(item.category.toLowerCase());

          await inventoryApi.createItem({
            name: item.name,
            unit: item.unit,
            current_quantity: item.quantity,
            min_threshold: item.minThreshold,
            category_id: categoryId,
            cost_per_unit: undefined
          });

          itemsCreated++;
        } catch (error) {
          console.error(`Failed to create item ${item.name}:`, error);
          itemsFailed++;
        }
      }

      return { categoriesCreated, itemsCreated, itemsFailed };
    },
    onSuccess: (results) => {
      setImportResults(results);
      setStep('complete');
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
    onError: (error: any) => {
      setErrors([`Import failed: ${error.message || 'Unknown error'}`]);
      setStep('preview');
    }
  });

  const handleImport = () => {
    setStep('importing');
    importMutation.mutate();
  };

  const handleReset = () => {
    setStep('input');
    setTemplateText('');
    setParsedItems([]);
    setErrors([]);
    setImportResults({ categoriesCreated: 0, itemsCreated: 0, itemsFailed: 0 });
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-coffee-dark rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-border">
          <div>
            <h2 className="text-xl font-heading text-neutral-text-dark dark:text-cream">
              Import from WhatsApp Template
            </h2>
            <p className="text-sm text-neutral-text-muted mt-1">
              Paste your WhatsApp inventory template to bulk import items
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-neutral-background rounded-lg transition-colors"
          >
            <X size={24} className="text-neutral-text-muted" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Errors */}
          {errors.length > 0 && (
            <div className="mb-4 p-4 bg-error/10 border border-error rounded-lg">
              <div className="flex items-start gap-2">
                <Warning size={20} className="text-error flex-shrink-0 mt-0.5" weight="fill" />
                <div className="flex-1">
                  {errors.map((error, i) => (
                    <p key={i} className="text-sm text-error">{error}</p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 1: Input */}
          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-text-dark dark:text-cream mb-2">
                  WhatsApp Template Text
                </label>
                <textarea
                  value={templateText}
                  onChange={(e) => setTemplateText(e.target.value)}
                  placeholder="Paste your WhatsApp inventory template here...

Example:
*DRY GROCERY*
Salt - 1
Sugar - 5kg
Rice - YES
..."
                  className="input-field w-full h-96 font-mono text-sm"
                  autoFocus
                />
              </div>

              <div className="bg-lily-green/10 border border-lily-green/30 rounded-lg p-4">
                <h3 className="font-medium text-lily-green dark:text-lily-green-light mb-2 text-sm">
                  Supported Formats:
                </h3>
                <ul className="text-xs text-neutral-text-muted space-y-1">
                  <li>• Numbers: 5, 10.5</li>
                  <li>• Fractions: ½, ¼, ¾</li>
                  <li>• Weights: 50g, 4kg, 500ml, 1L</li>
                  <li>• YES/NO: Converts to 1/0</li>
                  <li>• Categories: Lines starting with *CATEGORY NAME*</li>
                </ul>
              </div>
            </div>
          )}

          {/* Step 2: Preview */}
          {step === 'preview' && (
            <div className="space-y-4">
              <div className="bg-neutral-background rounded-lg p-4">
                <p className="text-sm text-neutral-text-muted">
                  Found <span className="font-bold text-lily-green">{parsedItems.length} items</span> across{' '}
                  <span className="font-bold text-lily-green">
                    {new Set(parsedItems.map(i => i.category)).size} categories
                  </span>
                </p>
              </div>

              <div className="border border-neutral-border rounded-lg overflow-hidden">
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-neutral-background sticky top-0">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-text-muted uppercase">
                          Category
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-text-muted uppercase">
                          Item Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-text-muted uppercase">
                          Quantity
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-text-muted uppercase">
                          Unit
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-neutral-text-muted uppercase">
                          Min Threshold
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-border">
                      {parsedItems.map((item, index) => (
                        <tr key={index} className="hover:bg-neutral-background/50">
                          <td className="px-4 py-3 text-sm text-neutral-text-dark dark:text-cream">
                            {item.category}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-neutral-text-dark dark:text-cream">
                            {item.name}
                          </td>
                          <td className="px-4 py-3 text-sm font-mono text-neutral-text-dark dark:text-cream">
                            {item.quantity}
                          </td>
                          <td className="px-4 py-3 text-sm text-neutral-text-muted">
                            {item.unit}
                          </td>
                          <td className="px-4 py-3 text-sm font-mono text-neutral-text-muted">
                            {item.minThreshold}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Importing */}
          {step === 'importing' && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin text-lily-green mb-4">
                <Upload size={48} />
              </div>
              <p className="text-lg font-medium text-neutral-text-dark dark:text-cream">
                Importing items...
              </p>
              <p className="text-sm text-neutral-text-muted mt-2">
                This may take a moment. Please don't close this window.
              </p>
            </div>
          )}

          {/* Step 4: Complete */}
          {step === 'complete' && (
            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center py-8">
                <div className="text-lily-green mb-4">
                  <CheckCircle size={64} weight="fill" />
                </div>
                <h3 className="text-xl font-heading text-neutral-text-dark dark:text-cream mb-2">
                  Import Complete!
                </h3>
                <p className="text-sm text-neutral-text-muted">
                  Your inventory items have been imported successfully.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="card p-4 text-center">
                  <div className="text-2xl font-bold text-lily-green dark:text-lily-green-light">
                    {importResults.categoriesCreated}
                  </div>
                  <div className="text-sm text-neutral-text-muted mt-1">
                    Categories Created
                  </div>
                </div>

                <div className="card p-4 text-center">
                  <div className="text-2xl font-bold text-lily-green dark:text-lily-green-light">
                    {importResults.itemsCreated}
                  </div>
                  <div className="text-sm text-neutral-text-muted mt-1">
                    Items Created
                  </div>
                </div>

                {importResults.itemsFailed > 0 && (
                  <div className="card p-4 text-center">
                    <div className="text-2xl font-bold text-error">
                      {importResults.itemsFailed}
                    </div>
                    <div className="text-sm text-neutral-text-muted mt-1">
                      Items Failed
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between gap-3 p-6 border-t border-neutral-border">
          {step === 'input' && (
            <>
              <button onClick={handleClose} className="btn-ghost">
                Cancel
              </button>
              <button onClick={handleParse} className="btn-primary">
                Parse Template
              </button>
            </>
          )}

          {step === 'preview' && (
            <>
              <button onClick={() => setStep('input')} className="btn-ghost">
                Back to Edit
              </button>
              <button
                onClick={handleImport}
                className="btn-primary flex items-center gap-2"
              >
                <Upload size={20} weight="fill" />
                Import {parsedItems.length} Items
              </button>
            </>
          )}

          {step === 'complete' && (
            <>
              <button onClick={handleReset} className="btn-ghost">
                Import Another Template
              </button>
              <button onClick={handleClose} className="btn-primary">
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

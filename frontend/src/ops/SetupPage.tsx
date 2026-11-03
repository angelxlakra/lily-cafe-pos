/**
 * Setup (owner only): the items grid, a form for one new item, categories,
 * the order the nightly count walks in, and the one-time list import.
 * The API enforces owner-only; the route and the ops bar hide it from others.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { inventoryApi } from '../api/inventory';
import {
  useCreateCategory, useCreateItem, useDeleteCategory, useInventoryCategories, useUpdateCategory,
} from '../hooks/useInventory';
import { describeApiError } from '../utils/apiError';
import type { InventoryCategory } from '../types/inventory';
import CountOrderEditor from './CountOrderEditor';
import InventorySetupGrid from './InventorySetupGrid';
import OpsConfirm from './OpsConfirm';
import TemplateImportModal from './TemplateImportModal';
import './setup.css';

const SECTIONS = [
  { id: 'setup-items', label: 'Items' },
  { id: 'setup-add', label: 'Add item' },
  { id: 'setup-categories', label: 'Categories' },
  { id: 'setup-order', label: 'Count order' },
  { id: 'setup-import', label: 'Import' },
];

export default function SetupPage() {
  const navigate = useNavigate();
  const { data: categories = [] } = useInventoryCategories();
  const [importing, setImporting] = useState(false);

  return (
    <>
      <h1>Setup</h1>
      <p className="muted">Items, categories and the order of the nightly count.</p>
      <div className="su-jump" role="group" aria-label="Jump to">
        {SECTIONS.map(({ id, label }) => (
          <button key={id} type="button" className="chip" onClick={() => document.getElementById(id)?.scrollIntoView({ block: 'start' })}>
            {label}
          </button>
        ))}
      </div>

      <section id="setup-items" className="su-sec" aria-labelledby="h-items">
        <h2 id="h-items">Items</h2>
        <InventorySetupGrid onDone={() => navigate('/admin/ops/inventory')} />
      </section>

      <section id="setup-add" className="su-sec" aria-labelledby="h-add">
        <h2 id="h-add">Add item</h2>
        <AddItem categories={categories} />
      </section>

      <section id="setup-categories" className="su-sec" aria-labelledby="h-categories">
        <h2 id="h-categories">Categories</h2>
        <Categories categories={categories} />
      </section>

      <section id="setup-order" className="su-sec" aria-labelledby="h-order">
        <h2 id="h-order">Count order</h2>
        <CountOrderEditor />
      </section>

      <section id="setup-import" className="su-sec" aria-labelledby="h-import">
        <h2 id="h-import">Import</h2>
        <p className="muted">One-time setup: paste the WhatsApp stock checklist to create its categories and items at once.</p>
        <button type="button" className="btn" onClick={() => setImporting(true)}>Import list</button>
        <TemplateImportModal isOpen={importing} onClose={() => setImporting(false)} existingCategories={categories} />
      </section>
    </>
  );
}

// Units a recipe can already measure in. Anything else (pcs, a packet, a bottle) needs a pack
// size before 25 g of it can be costed.
const MEASURED = new Set(['g', 'kg', 'ml', 'l']);
const PACK_UNITS = ['g', 'kg', 'ml', 'L', 'pcs'];
const OTHER_UNITS = ['pkt', 'bottle', 'tin', 'box', 'portion'];

function AddItem({ categories }: { categories: InventoryCategory[] }) {
  const createItem = useCreateItem();
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [unit, setUnit] = useState('pcs');
  const [quantity, setQuantity] = useState('0');
  const [threshold, setThreshold] = useState('5');
  // Blank means no price. Sending 0 is what left 98 items looking free.
  const [cost, setCost] = useState('');
  // "1 pcs = 500 g": blank means not set.
  const [packSize, setPackSize] = useState('');
  const [packUnit, setPackUnit] = useState('g');
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState<string | null>(null);

  const takesPack = !MEASURED.has(unit.trim().toLowerCase());

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAdded(null);
    const pack = takesPack
      ? (packSize.trim() !== '' ? { pack_size: Number(packSize), pack_unit: packUnit } : { pack_size: null, pack_unit: null })
      : {};
    try {
      await createItem.mutateAsync({
        name,
        category_id: categoryId ? Number(categoryId) : undefined,
        unit,
        current_quantity: Number(quantity),
        min_threshold: Number(threshold),
        cost_per_unit: cost.trim() === '' ? null : Number(cost),
        ...pack,
      });
      setAdded(name.trim());
      setName('');
      setQuantity('0');
      setCost('');
      setPackSize('');
    } catch (err) {
      setError(describeApiError(err));
    }
  };

  return (
    <form onSubmit={submit} className="ops-form su-add">
      <label>
        Name
        <input type="text" required value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Milk, Eggs" />
      </label>
      <div className="su-pair">
        <label>
          Category
          <select value={categoryId} onChange={e => setCategoryId(e.target.value)}>
            <option value="">None</option>
            {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
          </select>
        </label>
        <label>
          Unit
          <select value={unit} onChange={e => setUnit(e.target.value)}>
            <option value="pcs">Pieces (pcs)</option>
            <option value="kg">Kilograms (kg)</option>
            <option value="g">Grams (g)</option>
            <option value="L">Litres (L)</option>
            <option value="ml">Millilitres (ml)</option>
            {OTHER_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
      </div>

      {takesPack && (
        <label>
          <span>What one {unit} holds (optional)</span>
          <span className="su-pack">
            <span style={{ flex: 'none', color: 'var(--ops-fg)' }}>1 {unit} =</span>
            <input
              type="number" min="0" step="any" inputMode="decimal" value={packSize} placeholder="e.g. 500"
              onChange={e => setPackSize(e.target.value)}
            />
            <select aria-label="Pack unit" value={packUnit} onChange={e => setPackUnit(e.target.value)}>
              {PACK_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </span>
          <span>So a recipe can use it by weight or volume: 1 pack of butter = 500 g.</span>
        </label>
      )}

      <label>
        Stock right now
        <input type="number" min="0" step="0.01" value={quantity} onChange={e => setQuantity(e.target.value)} />
      </label>
      <div className="su-pair">
        <label>
          Alert below
          <input type="number" min="0" step="0.01" value={threshold} onChange={e => setThreshold(e.target.value)} />
        </label>
        <label>
          Cost per unit (₹)
          <input type="number" min="0" step="0.01" value={cost} placeholder="Not set" onChange={e => setCost(e.target.value)} />
        </label>
      </div>

      {error && <div role="alert" className="su-err">Not added. {error}</div>}
      {added && <div role="status" className="muted">Added {added}. It shows in the grid above.</div>}
      <div>
        <button type="submit" className="btn" disabled={createItem.isPending}>
          {createItem.isPending ? 'Adding…' : 'Add item'}
        </button>
      </div>
    </form>
  );
}

function Categories({ categories }: { categories: InventoryCategory[] }) {
  // Item counts per category come from the count sheet (active items only).
  const { data: groups = [] } = useQuery({
    queryKey: ['inventory', 'count-sheet'],
    queryFn: inventoryApi.getCountSheet,
  });
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const deleteCategory = useDeleteCategory();

  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [deleting, setDeleting] = useState<InventoryCategory | null>(null);
  const [notice, setNotice] = useState<{ id: number | 'new'; text: string } | null>(null);

  const itemCount = (id: number) => groups.find(group => group.category?.id === id)?.items.length ?? 0;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createCategory.mutateAsync({ name: newName.trim() });
      setNewName('');
      setNotice(null);
    } catch (error) {
      setNotice({ id: 'new', text: `Not added. ${describeApiError(error)}` });
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editName.trim() || editingId === null) return;
    try {
      await updateCategory.mutateAsync({ id: editingId, data: { name: editName.trim() } });
      setEditingId(null);
      setNotice(null);
    } catch (error) {
      setNotice({ id: editingId, text: `Not renamed. ${describeApiError(error)}` });
    }
  };

  const askDelete = (category: InventoryCategory) => {
    const count = itemCount(category.id);
    if (count > 0) {
      setNotice({ id: category.id, text: `Move or retire its ${count} item${count === 1 ? '' : 's'} first, in the grid above.` });
      return;
    }
    setNotice(null);
    setDeleting(category);
  };

  const confirmDelete = async () => {
    const category = deleting;
    setDeleting(null);
    if (!category) return;
    try {
      await deleteCategory.mutateAsync(category.id);
    } catch (error) {
      setNotice({ id: category.id, text: `Not deleted. ${describeApiError(error)}` });
    }
  };

  return (
    <div>
      <form onSubmit={handleCreate} className="su-inline" style={{ maxWidth: 640 }}>
        <input
          type="text"
          aria-label="New category"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="New category, e.g. Dairy, Dry grocery"
        />
        <button type="submit" className="btn" disabled={createCategory.isPending || !newName.trim()}>
          {createCategory.isPending ? 'Adding…' : 'Add category'}
        </button>
      </form>
      {notice?.id === 'new' && <div role="alert" className="su-err" style={{ color: 'var(--ops-bad)', fontWeight: 600 }}>{notice.text}</div>}

      {categories.length === 0 ? (
        <p className="muted">No categories yet. Add one, or import the WhatsApp checklist below.</p>
      ) : (
        <>
          <p className="muted" style={{ margin: '4px 0 0' }}>{categories.length} categor{categories.length === 1 ? 'y' : 'ies'}</p>
          <ul className="su-list">
            {categories.map(category => {
              const count = itemCount(category.id);
              return (
                <li key={category.id} style={{ paddingLeft: 12 }}>
                  {editingId === category.id ? (
                    <form onSubmit={handleUpdate} className="su-inline">
                      <input
                        type="text"
                        aria-label={`Name for ${category.name}`}
                        value={editName}
                        onChange={e => setEditName(e.target.value)}
                        autoFocus
                      />
                      <button type="submit" className="btn" disabled={updateCategory.isPending || !editName.trim()}>Save</button>
                      <button type="button" onClick={() => { setEditingId(null); setNotice(null); }} className="btn ghost">Cancel</button>
                    </form>
                  ) : (
                    <div className="su-line">
                      <div className="who">
                        <span className="nm">{category.name}</span>
                        <span className="muted">{count} item{count === 1 ? '' : 's'}</span>
                      </div>
                      <button
                        type="button"
                        className="text-btn"
                        onClick={() => { setEditingId(category.id); setEditName(category.name.trim()); setNotice(null); }}
                        aria-label={`Rename ${category.name}`}
                      >
                        Rename
                      </button>
                      <button type="button" className="text-btn bad" onClick={() => askDelete(category)} aria-label={`Delete ${category.name}`}>
                        Delete
                      </button>
                    </div>
                  )}
                  {notice?.id === category.id && (
                    <div role="alert" style={{ color: 'var(--ops-bad)', fontSize: 14, fontWeight: 600, paddingBottom: 8 }}>{notice.text}</div>
                  )}
                </li>
              );
            })}
          </ul>
        </>
      )}

      <OpsConfirm
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        onConfirm={confirmDelete}
        title={`Delete ${deleting?.name.trim() ?? 'category'}?`}
        message="It has no items, so nothing else changes."
        confirmText="Delete category"
        cancelText="Keep it"
      />
    </div>
  );
}

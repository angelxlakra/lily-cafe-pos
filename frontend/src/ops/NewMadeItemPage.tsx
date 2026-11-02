import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCreateItem, useInventoryCategories } from '../hooks/useInventory';
import { describeApiError } from '../utils/apiError';

const UNITS = ['kg', 'g', 'L', 'ml', 'pcs', 'pkt'];

/** Asks for the three things a made item needs, creates the inventory item, and opens its recipe. */
export default function NewMadeItemPage() {
  const navigate = useNavigate();
  const categories = useInventoryCategories();
  const create = useCreateItem();
  const [name, setName] = useState('');
  const [unit, setUnit] = useState('kg');
  const [categoryId, setCategoryId] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || create.isPending) return;
    create.mutate(
      {
        name: name.trim(), unit, current_quantity: 0, min_threshold: 0,
        ...(categoryId ? { category_id: Number(categoryId) } : {}),
      },
      { onSuccess: item => navigate(`/admin/ops/recipes/made/${item.id}`, { replace: true }) },
    );
  };

  return (
    <form onSubmit={submit} className="ops-form">
      <h1>New made item</h1>
      <p className="muted">Something the kitchen makes and then uses in dishes, like a masala or a sauce.</p>
      <label htmlFor="mi-name">Name
        <input id="mi-name" autoFocus required value={name} onChange={e => setName(e.target.value)} />
      </label>
      <label htmlFor="mi-unit">Unit
        <select id="mi-unit" value={unit} onChange={e => setUnit(e.target.value)}>
          {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
      </label>
      <label htmlFor="mi-cat">Category
        <select id="mi-cat" value={categoryId} onChange={e => setCategoryId(e.target.value)}>
          <option value="">No category</option>
          {categories.data?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </label>
      {create.isError && <p className="err">{describeApiError(create.error)}</p>}
      <div className="ops-actions">
        <button type="submit" className="btn" disabled={!name.trim() || create.isPending}>Create and add ingredients</button>
        <Link to="/admin/ops/recipes" className="btn ghost ops-link-btn">Cancel</Link>
      </div>
    </form>
  );
}

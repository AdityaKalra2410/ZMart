import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Trash2, Plus, Package, Users, ShoppingBag } from 'lucide-react';

const AdminDashboard = () => {
  const { role } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [products, setProducts] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New product form
  const [newProduct, setNewProduct] = useState({ name: '', price: '', category_id: '', stock: '', image: '', description: '' });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (role !== 'admin') {
      navigate('/');
      return;
    }
    fetchAll();
  }, [role, navigate]);

  const fetchAll = async () => {
    const [prodRes, catRes, orderRes] = await Promise.all([
      supabase.from('products').select('*, categories(name)'),
      supabase.from('categories').select('*'),
      supabase.from('orders').select('*').order('created_at', { ascending: false }).limit(20),
    ]);
    setProducts(prodRes.data || []);
    setCategories(catRes.data || []);
    setOrders(orderRes.data || []);
    setLoading(false);
  };

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    const { error } = await supabase.from('products').insert({
      name: newProduct.name,
      price: parseFloat(newProduct.price),
      category_id: newProduct.category_id || null,
      stock: parseInt(newProduct.stock) || 0,
      image: newProduct.image,
      description: newProduct.description,
    });
    if (error) {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
    } else {
      toast({ title: 'Product added!' });
      setNewProduct({ name: '', price: '', category_id: '', stock: '', image: '', description: '' });
      setShowForm(false);
      fetchAll();
    }
  };

  const handleDeleteProduct = async (id: string) => {
    const { error } = await supabase.from('products').delete().eq('id', id);
    if (error) {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
    } else {
      toast({ title: 'Product deleted' });
      fetchAll();
    }
  };

  if (loading) return <div className="container mx-auto px-4 py-12"><div className="animate-pulse h-96 bg-muted rounded-xl" /></div>;

  return (
    <div className="container mx-auto px-4 py-8 animate-fade-in">
      <h1 className="font-heading text-3xl font-bold">Admin Dashboard</h1>

      {/* Stats */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-6 flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <ShoppingBag className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Products</p>
            <p className="font-heading text-2xl font-bold">{products.length}</p>
          </div>
        </div>
        <div className="rounded-xl border bg-card p-6 flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
            <Package className="h-6 w-6 text-accent" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Orders</p>
            <p className="font-heading text-2xl font-bold">{orders.length}</p>
          </div>
        </div>
        <div className="rounded-xl border bg-card p-6 flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary">
            <Users className="h-6 w-6 text-secondary-foreground" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Categories</p>
            <p className="font-heading text-2xl font-bold">{categories.length}</p>
          </div>
        </div>
      </div>

      {/* Products management */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-bold">Products</h2>
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4 mr-1" /> Add Product
          </Button>
        </div>

        {showForm && (
          <form onSubmit={handleAddProduct} className="mt-4 rounded-xl border bg-card p-6 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input required value={newProduct.name} onChange={e => setNewProduct(p => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Price (₹)</Label>
                <Input type="number" step="0.01" required value={newProduct.price} onChange={e => setNewProduct(p => ({ ...p, price: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={newProduct.category_id}
                  onChange={e => setNewProduct(p => ({ ...p, category_id: e.target.value }))}
                >
                  <option value="">Select category</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Stock</Label>
                <Input type="number" required value={newProduct.stock} onChange={e => setNewProduct(p => ({ ...p, stock: e.target.value }))} />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Image URL</Label>
                <Input value={newProduct.image} onChange={e => setNewProduct(p => ({ ...p, image: e.target.value }))} placeholder="https://..." />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Description</Label>
                <Input value={newProduct.description} onChange={e => setNewProduct(p => ({ ...p, description: e.target.value }))} />
              </div>
            </div>
            <Button type="submit">Save Product</Button>
          </form>
        )}

        <div className="mt-4 rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Product</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground hidden sm:table-cell">Category</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Price</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Stock</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {products.map(p => (
                <tr key={p.id} className="bg-card">
                  <td className="px-4 py-3 flex items-center gap-2">
                    <img src={p.image || '/placeholder.svg'} alt="" className="h-8 w-8 rounded object-cover" />
                    <span className="font-medium">{p.name}</span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">{p.categories?.name || '—'}</td>
                  <td className="px-4 py-3 text-right">₹{p.price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">{p.stock}</td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDeleteProduct(p.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="mt-8">
        <h2 className="font-heading text-xl font-bold">Recent Orders</h2>
        <div className="mt-4 space-y-3">
          {orders.map(order => (
            <div key={order.id} className="flex items-center justify-between rounded-xl border bg-card p-4">
              <div>
                <p className="text-sm font-medium">#{order.id.slice(0, 8)}</p>
                <p className="text-xs text-muted-foreground">{new Date(order.created_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium capitalize">{order.status}</span>
                <span className="font-bold text-primary">₹{order.total_price.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;

import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import ProductCard from '@/components/ProductCard';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, Truck, Shield, Clock } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
  stock: number;
  category_id: string | null;
  categories?: { name: string } | null;
}

interface Category {
  id: string;
  name: string;
}

const Index = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const [prodRes, catRes] = await Promise.all([
        supabase.from('products').select('*, categories(name)'),
        supabase.from('categories').select('*'),
      ]);
      setProducts((prodRes.data as Product[]) || []);
      setCategories((catRes.data as Category[]) || []);
      setLoading(false);
    };
    fetchData();
  }, []);

  const filtered = products.filter(p => {
    const matchesCategory = !selectedCategory || p.category_id === selectedCategory;
    const matchesSearch = !search || p.name.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="hero-gradient px-4 py-16 text-center">
        <div className="container mx-auto max-w-3xl animate-fade-in">
          <h1 className="font-heading text-4xl font-bold text-primary-foreground md:text-5xl">
            Fresh Groceries,<br />Delivered to Your Door
          </h1>
          <p className="mt-4 text-lg text-primary-foreground/80">
            Save big on daily essentials. Shop smart with Zmart!
          </p>
          <div className="mx-auto mt-8 flex max-w-md items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search products..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-10 bg-card border-0"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features strip */}
      <section className="border-b bg-card">
        <div className="container mx-auto flex flex-wrap items-center justify-center gap-8 py-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-2"><Truck className="h-4 w-4 text-primary" /> Free delivery over ₹500</span>
          <span className="flex items-center gap-2"><Clock className="h-4 w-4 text-primary" /> Same day delivery</span>
          <span className="flex items-center gap-2"><Shield className="h-4 w-4 text-primary" /> 100% quality assured</span>
        </div>
      </section>

      {/* Category filters */}
      <section className="container mx-auto px-4 pt-8">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={selectedCategory === null ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory(null)}
          >
            All
          </Button>
          {categories.map(cat => (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.name}
            </Button>
          ))}
        </div>
      </section>

      {/* Products grid */}
      <section className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="animate-pulse rounded-xl bg-muted aspect-[3/4]" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center text-muted-foreground">
            <p className="text-lg">No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {filtered.map(product => (
              <ProductCard
                key={product.id}
                id={product.id}
                name={product.name}
                price={product.price}
                image={product.image}
                stock={product.stock}
                category={product.categories?.name}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Index;

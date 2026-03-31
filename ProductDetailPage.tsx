import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useCart } from '@/contexts/CartContext';
import { Button } from '@/components/ui/button';
import { ShoppingCart, ArrowLeft, Minus, Plus } from 'lucide-react';

const ProductDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const [product, setProduct] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      const { data } = await supabase
        .from('products')
        .select('*, categories(name)')
        .eq('id', id!)
        .maybeSingle();
      setProduct(data);
      setLoading(false);
    };
    if (id) fetch();
  }, [id]);

  if (loading) return <div className="container mx-auto px-4 py-12"><div className="animate-pulse h-96 rounded-xl bg-muted" /></div>;
  if (!product) return <div className="container mx-auto px-4 py-20 text-center text-muted-foreground">Product not found</div>;

  const handleAdd = () => {
    for (let i = 0; i < quantity; i++) {
      addItem({ id: product.id, name: product.name, price: product.price, image: product.image });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 animate-fade-in">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-4">
        <ArrowLeft className="h-4 w-4 mr-1" /> Back
      </Button>

      <div className="grid gap-8 md:grid-cols-2">
        <div className="overflow-hidden rounded-xl bg-muted aspect-square">
          <img src={product.image || '/placeholder.svg'} alt={product.name} className="h-full w-full object-cover" />
        </div>

        <div className="flex flex-col justify-center space-y-4">
          {product.categories?.name && (
            <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{product.categories.name}</span>
          )}
          <h1 className="font-heading text-3xl font-bold">{product.name}</h1>
          <p className="text-muted-foreground">{product.description || 'No description available.'}</p>
          <p className="text-3xl font-bold text-primary">₹{product.price.toFixed(2)}</p>

          <div className="flex items-center gap-2 text-sm">
            <span className={`font-medium ${product.stock > 0 ? 'text-primary' : 'text-destructive'}`}>
              {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center rounded-lg border">
              <Button variant="ghost" size="icon" onClick={() => setQuantity(Math.max(1, quantity - 1))} className="h-9 w-9">
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-10 text-center font-medium">{quantity}</span>
              <Button variant="ghost" size="icon" onClick={() => setQuantity(Math.min(product.stock, quantity + 1))} className="h-9 w-9">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button size="lg" disabled={product.stock === 0} onClick={handleAdd}>
              <ShoppingCart className="h-4 w-4 mr-2" /> Add to Cart
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;

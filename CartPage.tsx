import { useNavigate } from 'react-router-dom';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Minus, Plus, Trash2, ShoppingBag } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const CartPage = () => {
  const { items, updateQuantity, removeItem, clearCart, totalPrice } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleCheckout = async () => {
    if (!user) {
      toast({ title: 'Please login', description: 'You need to be logged in to place an order', variant: 'destructive' });
      navigate('/login');
      return;
    }

    // Create order
    const { data: order, error: orderError } = await supabase
      .from('orders')
      .insert({ user_id: user.id, total_price: totalPrice, status: 'pending' })
      .select()
      .single();

    if (orderError || !order) {
      toast({ title: 'Order failed', description: orderError?.message || 'Unknown error', variant: 'destructive' });
      return;
    }

    // Create order items
    const orderItems = items.map(item => ({
      order_id: order.id,
      product_id: item.id,
      quantity: item.quantity,
      price: item.price,
    }));

    const { error: itemsError } = await supabase.from('order_items').insert(orderItems);
    if (itemsError) {
      toast({ title: 'Order items failed', description: itemsError.message, variant: 'destructive' });
      return;
    }

    clearCart();
    toast({ title: 'Order placed!', description: `Order total: ₹${totalPrice.toFixed(2)}` });
    navigate('/orders');
  };

  if (items.length === 0) {
    return (
      <div className="container mx-auto flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <ShoppingBag className="h-16 w-16 text-muted-foreground/40" />
        <h1 className="mt-4 font-heading text-2xl font-bold">Your cart is empty</h1>
        <p className="mt-2 text-muted-foreground">Add some products to get started!</p>
        <Button className="mt-6" onClick={() => navigate('/')}>Browse Products</Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 animate-fade-in">
      <h1 className="font-heading text-3xl font-bold">Shopping Cart</h1>
      <div className="mt-6 grid gap-8 lg:grid-cols-3">
        {/* Items */}
        <div className="space-y-4 lg:col-span-2">
          {items.map(item => (
            <div key={item.id} className="flex gap-4 rounded-xl border bg-card p-4">
              <img src={item.image || '/placeholder.svg'} alt={item.name} className="h-20 w-20 rounded-lg object-cover" />
              <div className="flex flex-1 flex-col justify-between">
                <div>
                  <h3 className="font-heading font-semibold">{item.name}</h3>
                  <p className="text-sm text-muted-foreground">₹{item.price.toFixed(2)} each</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center rounded-lg border">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateQuantity(item.id, item.quantity - 1)}>
                      <Minus className="h-3 w-3" />
                    </Button>
                    <span className="w-8 text-center text-sm">{item.quantity}</span>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateQuantity(item.id, item.quantity + 1)}>
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => removeItem(item.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <p className="font-bold text-primary">₹{(item.price * item.quantity).toFixed(2)}</p>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="rounded-xl border bg-card p-6 h-fit sticky top-20">
          <h2 className="font-heading text-xl font-bold">Order Summary</h2>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>₹{totalPrice.toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Delivery</span><span className="text-primary font-medium">{totalPrice >= 500 ? 'FREE' : '₹40.00'}</span></div>
          </div>
          <div className="mt-4 border-t pt-4 flex justify-between font-heading text-lg font-bold">
            <span>Total</span>
            <span className="text-primary">₹{(totalPrice + (totalPrice >= 500 ? 0 : 40)).toFixed(2)}</span>
          </div>
          <Button className="mt-6 w-full" size="lg" onClick={handleCheckout}>Place Order</Button>
        </div>
      </div>
    </div>
  );
};

export default CartPage;

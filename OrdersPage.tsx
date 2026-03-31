import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Package } from 'lucide-react';

const OrdersPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    const fetch = async () => {
      const { data } = await supabase
        .from('orders')
        .select('*, order_items(*, products(name, image))')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });
      setOrders(data || []);
      setLoading(false);
    };
    fetch();
  }, [user, navigate]);

  const statusColors: Record<string, string> = {
    pending: 'bg-secondary text-secondary-foreground',
    confirmed: 'bg-primary/10 text-primary',
    shipped: 'bg-accent/10 text-accent',
    delivered: 'bg-primary text-primary-foreground',
    cancelled: 'bg-destructive/10 text-destructive',
  };

  if (loading) return <div className="container mx-auto px-4 py-12"><div className="animate-pulse space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 rounded-xl bg-muted"/>)}</div></div>;

  return (
    <div className="container mx-auto px-4 py-8 animate-fade-in">
      <h1 className="font-heading text-3xl font-bold">My Orders</h1>

      {orders.length === 0 ? (
        <div className="mt-20 text-center">
          <Package className="mx-auto h-16 w-16 text-muted-foreground/40" />
          <p className="mt-4 text-lg text-muted-foreground">No orders yet</p>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {orders.map(order => (
            <div key={order.id} className="rounded-xl border bg-card p-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm text-muted-foreground">Order #{order.id.slice(0, 8)}</p>
                  <p className="text-sm text-muted-foreground">{new Date(order.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${statusColors[order.status] || ''}`}>
                    {order.status}
                  </span>
                  <span className="font-heading font-bold text-primary">₹{order.total_price.toFixed(2)}</span>
                </div>
              </div>
              {order.order_items?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {order.order_items.map((item: any) => (
                    <div key={item.id} className="flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5">
                      <img src={item.products?.image || '/placeholder.svg'} alt="" className="h-8 w-8 rounded object-cover" />
                      <span className="text-sm">{item.products?.name} × {item.quantity}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OrdersPage;

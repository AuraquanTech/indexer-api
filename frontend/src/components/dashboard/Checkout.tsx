'use client';

import React, { useState, useEffect } from 'react';
import {
    CreditCard,
    Package,
    DollarSign,
    Link as LinkIcon,
    Plus,
    Copy,
    Check,
    ExternalLink,
    ShoppingCart,
    TrendingUp,
    Users,
    Zap
} from 'lucide-react';

interface Product {
    id: string;
    name: string;
    description: string;
    price_cents: number;
    status: string;
    stripe_price_id?: string;
    total_sales: number;
    total_revenue_cents: number;
    features: string[];
}

interface PaymentStatus {
    status: string;
    stripe_configured: boolean;
    email_configured: boolean;
    products_count: number;
    orders_count: number;
}

export function Checkout() {
    const [products, setProducts] = useState<Product[]>([]);
    const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [copiedLink, setCopiedLink] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newProduct, setNewProduct] = useState({
        name: '',
        description: '',
        price: '',
        features: ''
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [statusRes, productsRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/payments/status'),
                fetch('http://localhost:8000/api/v1/payments/products')
            ]);

            if (statusRes.ok) {
                setPaymentStatus(await statusRes.json());
            }
            if (productsRes.ok) {
                setProducts(await productsRes.json());
            }
        } catch (error) {
            console.error('Error fetching payment data:', error);
        } finally {
            setLoading(false);
        }
    };

    const createProduct = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/v1/payments/products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newProduct.name,
                    description: newProduct.description,
                    price_cents: Math.round(parseFloat(newProduct.price) * 100),
                    features: newProduct.features.split('\n').filter(f => f.trim())
                })
            });

            if (res.ok) {
                const product = await res.json();
                setProducts([...products, product]);
                setShowCreateForm(false);
                setNewProduct({ name: '', description: '', price: '', features: '' });
            }
        } catch (error) {
            console.error('Error creating product:', error);
        }
    };

    const getCheckoutLink = async (productId: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/payments/checkout/${productId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    success_url: `${window.location.origin}/checkout/success`,
                    cancel_url: `${window.location.origin}/checkout/cancel`
                })
            });

            if (res.ok) {
                const { checkout_url } = await res.json();
                window.open(checkout_url, '_blank');
            }
        } catch (error) {
            console.error('Error creating checkout:', error);
        }
    };

    const getPaymentLink = async (productId: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/payments/payment-link/${productId}`, {
                method: 'POST'
            });

            if (res.ok) {
                const { payment_link } = await res.json();
                await navigator.clipboard.writeText(payment_link);
                setCopiedLink(productId);
                setTimeout(() => setCopiedLink(null), 2000);
            }
        } catch (error) {
            console.error('Error creating payment link:', error);
        }
    };

    const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#00f3ff]"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-[#00f3ff] flex items-center gap-2">
                        <span className="text-[#ff003c]">///</span> CHECKOUT & PAYMENTS
                    </h2>
                    <p className="text-gray-400 mt-1">Sell your products with one-click checkout</p>
                </div>
                <button
                    onClick={() => setShowCreateForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#00f3ff] to-[#7000ff] text-black font-semibold rounded-lg hover:opacity-90 transition"
                >
                    <Plus className="w-4 h-4" />
                    New Product
                </button>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-4 gap-4">
                <div className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg p-4">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">STRIPE STATUS</span>
                        <CreditCard className={`w-5 h-5 ${paymentStatus?.stripe_configured ? 'text-[#00ff88]' : 'text-[#ff003c]'}`} />
                    </div>
                    <div className={`text-xl font-bold mt-2 ${paymentStatus?.stripe_configured ? 'text-[#00ff88]' : 'text-[#ff003c]'}`}>
                        {paymentStatus?.stripe_configured ? 'Connected' : 'Not Connected'}
                    </div>
                </div>

                <div className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg p-4">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">TOTAL PRODUCTS</span>
                        <Package className="w-5 h-5 text-[#7000ff]" />
                    </div>
                    <div className="text-xl font-bold text-white mt-2">
                        {paymentStatus?.products_count || 0}
                    </div>
                </div>

                <div className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg p-4">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">TOTAL ORDERS</span>
                        <ShoppingCart className="w-5 h-5 text-[#00f3ff]" />
                    </div>
                    <div className="text-xl font-bold text-white mt-2">
                        {paymentStatus?.orders_count || 0}
                    </div>
                </div>

                <div className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg p-4">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">EMAIL STATUS</span>
                        <Zap className={`w-5 h-5 ${paymentStatus?.email_configured ? 'text-[#00ff88]' : 'text-[#ff003c]'}`} />
                    </div>
                    <div className={`text-xl font-bold mt-2 ${paymentStatus?.email_configured ? 'text-[#00ff88]' : 'text-[#ff003c]'}`}>
                        {paymentStatus?.email_configured ? 'Active' : 'Not Configured'}
                    </div>
                </div>
            </div>

            {/* Create Product Modal */}
            {showCreateForm && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
                    <div className="bg-[#111118] border border-[#1a1a2e] rounded-xl p-6 w-full max-w-md">
                        <h3 className="text-xl font-bold text-[#00f3ff] mb-4">Create New Product</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-gray-400 text-sm mb-1">Product Name</label>
                                <input
                                    type="text"
                                    value={newProduct.name}
                                    onChange={e => setNewProduct({ ...newProduct, name: e.target.value })}
                                    className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg px-4 py-2 text-white focus:border-[#00f3ff] focus:outline-none"
                                    placeholder="My Awesome Product"
                                />
                            </div>

                            <div>
                                <label className="block text-gray-400 text-sm mb-1">Description</label>
                                <textarea
                                    value={newProduct.description}
                                    onChange={e => setNewProduct({ ...newProduct, description: e.target.value })}
                                    className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg px-4 py-2 text-white focus:border-[#00f3ff] focus:outline-none h-24 resize-none"
                                    placeholder="Describe your product..."
                                />
                            </div>

                            <div>
                                <label className="block text-gray-400 text-sm mb-1">Price (USD)</label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        type="number"
                                        value={newProduct.price}
                                        onChange={e => setNewProduct({ ...newProduct, price: e.target.value })}
                                        className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg pl-10 pr-4 py-2 text-white focus:border-[#00f3ff] focus:outline-none"
                                        placeholder="49.99"
                                        step="0.01"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-gray-400 text-sm mb-1">Features (one per line)</label>
                                <textarea
                                    value={newProduct.features}
                                    onChange={e => setNewProduct({ ...newProduct, features: e.target.value })}
                                    className="w-full bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg px-4 py-2 text-white focus:border-[#00f3ff] focus:outline-none h-20 resize-none font-mono text-sm"
                                    placeholder="Feature 1&#10;Feature 2&#10;Feature 3"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setShowCreateForm(false)}
                                className="flex-1 px-4 py-2 border border-[#1a1a2e] text-gray-400 rounded-lg hover:bg-[#1a1a2e] transition"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={createProduct}
                                disabled={!newProduct.name || !newProduct.price}
                                className="flex-1 px-4 py-2 bg-gradient-to-r from-[#00f3ff] to-[#7000ff] text-black font-semibold rounded-lg hover:opacity-90 transition disabled:opacity-50"
                            >
                                Create Product
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Products Grid */}
            <div className="grid grid-cols-2 gap-4">
                {products.map(product => (
                    <div
                        key={product.id}
                        className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-xl p-5 hover:border-[#00f3ff33] transition"
                    >
                        <div className="flex items-start justify-between mb-3">
                            <div>
                                <h3 className="text-lg font-semibold text-white">{product.name}</h3>
                                <p className="text-gray-400 text-sm mt-1 line-clamp-2">{product.description}</p>
                            </div>
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                                product.status === 'active'
                                    ? 'bg-[#00ff8833] text-[#00ff88]'
                                    : 'bg-[#ff003c33] text-[#ff003c]'
                            }`}>
                                {product.status.toUpperCase()}
                            </div>
                        </div>

                        <div className="text-3xl font-bold text-[#00f3ff] mb-4">
                            {formatPrice(product.price_cents)}
                        </div>

                        {product.features.length > 0 && (
                            <ul className="space-y-1 mb-4">
                                {product.features.slice(0, 3).map((feature, i) => (
                                    <li key={i} className="text-sm text-gray-400 flex items-center gap-2">
                                        <Check className="w-3 h-3 text-[#00ff88]" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>
                        )}

                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                            <TrendingUp className="w-4 h-4" />
                            <span>{product.total_sales} sales</span>
                            <span className="mx-2">•</span>
                            <DollarSign className="w-4 h-4" />
                            <span>{formatPrice(product.total_revenue_cents)} revenue</span>
                        </div>

                        <div className="flex gap-2">
                            <button
                                onClick={() => getCheckoutLink(product.id)}
                                disabled={!paymentStatus?.stripe_configured || product.status !== 'active'}
                                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-[#00f3ff] text-black font-medium rounded-lg hover:bg-[#00f3ff]/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <ExternalLink className="w-4 h-4" />
                                Buy Now
                            </button>
                            <button
                                onClick={() => getPaymentLink(product.id)}
                                disabled={!paymentStatus?.stripe_configured || product.status !== 'active'}
                                className="flex items-center justify-center gap-2 px-3 py-2 border border-[#1a1a2e] text-gray-300 rounded-lg hover:bg-[#1a1a2e] transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {copiedLink === product.id ? (
                                    <Check className="w-4 h-4 text-[#00ff88]" />
                                ) : (
                                    <Copy className="w-4 h-4" />
                                )}
                            </button>
                        </div>
                    </div>
                ))}

                {products.length === 0 && (
                    <div className="col-span-2 text-center py-12 text-gray-500">
                        <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No products yet. Create your first product to start selling!</p>
                    </div>
                )}
            </div>

            {/* Quick Setup Guide */}
            {!paymentStatus?.stripe_configured && (
                <div className="bg-[#ff003c11] border border-[#ff003c33] rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-[#ff003c] mb-3">⚠️ Stripe Not Connected</h3>
                    <p className="text-gray-400 mb-4">
                        To accept payments, add your Stripe secret key to <code className="text-[#00f3ff] bg-[#0a0a0f] px-2 py-1 rounded">~/.ai-credentials/api-keys.env</code>
                    </p>
                    <pre className="bg-[#0a0a0f] border border-[#1a1a2e] rounded-lg p-4 text-sm font-mono text-gray-300 overflow-x-auto">
{`STRIPE_SECRET_KEY=sk_live_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key_here`}
                    </pre>
                    <p className="text-gray-500 text-sm mt-3">
                        Get your keys at <a href="https://dashboard.stripe.com/apikeys" target="_blank" className="text-[#00f3ff] hover:underline">dashboard.stripe.com/apikeys</a>
                    </p>
                </div>
            )}
        </div>
    );
}

export default Checkout;

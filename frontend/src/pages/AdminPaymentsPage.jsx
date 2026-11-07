import React, { useState, useEffect } from "react";
import { 
  CreditCard, 
  Search, 
  Filter, 
  Calendar, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Clock, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  TrendingUp
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

const PAYMENT_STATUSES = ["SUCCESS", "PENDING", "FAILED", "REFUNDED"];

const PAYMENT_METHODS = [
  "UPI",
  "CREDIT_CARD",
  "DEBIT_CARD",
  "NET_BANKING",
  "WALLET",
  "CASH_ON_DELIVERY",
];

export const AdminPaymentsPage = () => {
  const [payments, setPayments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [methodFilter, setMethodFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (methodFilter) params.method = methodFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const resp = await adminApi.getPayments(params);
      if (resp.data.success) {
        setPayments(resp.data.data.items || []);
        setTotal(resp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load payment transactions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, statusFilter, methodFilter, startDate, endDate]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const getStatusBadge = (st) => {
    const colors = {
      SUCCESS: "bg-emerald-50 text-emerald-700 border-emerald-200",
      PENDING: "bg-amber-50 text-amber-800 border-amber-200",
      FAILED: "bg-red-50 text-red-700 border-red-200",
      REFUNDED: "bg-purple-50 text-purple-700 border-purple-200",
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${colors[st] || "bg-stone-100 text-stone-700 border-stone-200"}`}>
        {st}
      </span>
    );
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <AdminLayout
      title="Payment Monitoring"
      subtitle="Auditable record of payment attempts, transaction references, methods, and verification states"
      actions={
        <button
          onClick={fetchData}
          disabled={loading}
          className="p-2 border border-stone-300 rounded-xl bg-white hover:bg-stone-50 text-stone-700"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-purple-600" : ""}`} />
        </button>
      }
    >
      {/* Notifications */}
      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs flex flex-wrap items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transaction ref or order ref..."
            className="w-full pl-9 pr-3 py-2 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500"
          />
        </form>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Payment States</option>
          {PAYMENT_STATUSES.map((st) => (
            <option key={st} value={st}>
              {st}
            </option>
          ))}
        </select>

        <select
          value={methodFilter}
          onChange={(e) => {
            setMethodFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Payment Methods</option>
          {PAYMENT_METHODS.map((m) => (
            <option key={m} value={m}>
              {m.replace(/_/g, " ")}
            </option>
          ))}
        </select>

        <div className="flex items-center space-x-1.5 text-xs">
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
            title="Start Date"
          />
          <span className="text-stone-400">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
            className="px-2 py-1.5 border border-stone-200 rounded-xl text-xs focus:ring-2 focus:ring-purple-500 bg-white"
            title="End Date"
          />
        </div>

        {(search || statusFilter || methodFilter || startDate || endDate) && (
          <button
            onClick={() => {
              setSearch("");
              setStatusFilter("");
              setMethodFilter("");
              setStartDate("");
              setEndDate("");
              setPage(1);
            }}
            className="text-xs text-purple-600 font-bold hover:underline"
          >
            Reset
          </button>
        )}

        <div className="ml-auto text-xs text-stone-500 font-medium">
          Total Records: <strong className="text-charcoal-900">{total}</strong>
        </div>
      </div>

      {/* Payments Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Transaction Ref</th>
                <th className="py-3 px-4">Order Number</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Payment Method</th>
                <th className="py-3 px-4">State</th>
                <th className="py-3 px-4">Initiated At</th>
                <th className="py-3 px-4 text-right">Gateway ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-stone-400 font-medium">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                    Loading payment records...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-stone-400 font-medium">
                    <CreditCard className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                    No payment records match the specified filters.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.payment_id} className="hover:bg-stone-50/60 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-charcoal-900">
                      {p.transaction_reference}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-purple-700">
                      #{p.order_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <p className="font-bold text-charcoal-900">{p.customer_name}</p>
                      <span className="text-[10px] text-stone-400">{p.customer_email}</span>
                    </td>
                    <td className="py-3.5 px-4 font-black text-charcoal-900">
                      ₹{Number(p.amount).toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-200">
                        {p.payment_method?.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(p.payment_status)}
                    </td>
                    <td className="py-3.5 px-4 text-stone-500">
                      {new Date(p.initiated_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-[11px] text-stone-400">
                      {p.gateway_payment_id || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 bg-stone-50 border-t border-stone-200 flex items-center justify-between text-xs">
            <span className="text-stone-500">
              Page <strong>{page}</strong> of <strong>{totalPages}</strong>
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

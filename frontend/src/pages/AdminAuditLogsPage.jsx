import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  Search, 
  Filter, 
  Calendar, 
  Clock, 
  User, 
  FileText, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Database
} from "lucide-react";
import { AdminLayout } from "../components/AdminLayout";
import { adminApi } from "../services/api";

const COMMON_ACTIONS = [
  "USER_ACTIVATION",
  "ROLE_CHANGE",
  "KITCHEN_CREATED",
  "KITCHEN_UPDATED",
  "KITCHEN_STATUS_CHANGE",
  "STAFF_PROVISIONED",
  "STAFF_REASSIGNED",
  "MENU_STATUS_CHANGE",
  "CATEGORY_CREATED",
  "CATEGORY_UPDATED",
  "ORDER_CANCELLED_ADMIN",
  "COURIER_ASSIGNED",
  "COUPON_CREATED",
  "COUPON_UPDATED",
];

const ENTITY_TYPES = [
  "user",
  "kitchen",
  "kitchen_staff",
  "menu_item",
  "category",
  "order",
  "delivery",
  "coupon",
];

export const AdminAuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchLogs = async () => {
    setLoading(true);
    try {
      setErrorMsg("");
      const params = { page, page_size: pageSize };
      if (actionFilter) params.action = actionFilter;
      if (entityFilter) params.entity_type = entityFilter;

      const resp = await adminApi.getAuditLogs(params);
      if (resp.data.success) {
        setLogs(resp.data.data.items || []);
        setTotal(resp.data.data.meta?.total_count || 0);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to load audit security logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, entityFilter]);

  const toggleExpand = (auditId) => {
    setExpandedId((prev) => (prev === auditId ? null : auditId));
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <AdminLayout
      title="Administrative Audit Security Log"
      subtitle="Immutable compliance record of administrative actions, role escalations, mutations, and facility adjustments"
      actions={
        <button
          onClick={fetchLogs}
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
        <div className="flex items-center space-x-2 text-xs font-bold text-stone-600">
          <Filter className="w-4 h-4 text-purple-600" />
          <span>Audit Filters:</span>
        </div>

        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Action Types</option>
          {COMMON_ACTIONS.map((act) => (
            <option key={act} value={act}>
              {act.replace(/_/g, " ")}
            </option>
          ))}
        </select>

        <select
          value={entityFilter}
          onChange={(e) => {
            setEntityFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-stone-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-purple-500 bg-white"
        >
          <option value="">All Entity Types</option>
          {ENTITY_TYPES.map((et) => (
            <option key={et} value={et}>
              {et.toUpperCase()}
            </option>
          ))}
        </select>

        {(actionFilter || entityFilter) && (
          <button
            onClick={() => {
              setActionFilter("");
              setEntityFilter("");
              setPage(1);
            }}
            className="text-xs text-purple-600 font-bold hover:underline"
          >
            Clear Filters
          </button>
        )}

        <div className="ml-auto text-xs text-stone-500 font-medium">
          Logged Events: <strong className="text-charcoal-900">{total}</strong>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Administrator</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Target Entity</th>
                <th className="py-3 px-4">Entity ID</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-stone-400 font-medium">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-purple-600" />
                    Loading audit records...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-stone-400 font-medium">
                    <ShieldAlert className="w-8 h-8 mx-auto mb-2 text-stone-300" />
                    No audit records match the selected criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <React.Fragment key={log.audit_id}>
                    <tr 
                      onClick={() => toggleExpand(log.audit_id)}
                      className="hover:bg-stone-50/60 transition cursor-pointer"
                    >
                      <td className="py-3.5 px-4 font-mono text-stone-500 text-[11px]">
                        {new Date(log.created_at).toLocaleString([], {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-[10px] shrink-0">
                            {log.actor_name?.[0] || "A"}
                          </div>
                          <div>
                            <p className="font-bold text-charcoal-900">{log.actor_name}</p>
                            <span className="text-[10px] text-stone-400 font-mono">{log.actor_email}</span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono uppercase font-bold text-stone-600">
                        {log.entity_type}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-stone-500">
                        #{log.entity_id}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button className="text-stone-400 hover:text-charcoal-900 p-1">
                          {expandedId === log.audit_id ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      </td>
                    </tr>
                    {expandedId === log.audit_id && (
                      <tr className="bg-stone-50/80">
                        <td colSpan={6} className="p-4 border-t border-stone-200">
                          <div className="bg-charcoal-950 text-stone-200 p-3 rounded-xl font-mono text-[11px] overflow-x-auto shadow-inner">
                            <span className="text-stone-400 text-[10px] block mb-1 uppercase font-bold">
                              Structured Audit Payload:
                            </span>
                            <pre>{JSON.stringify(log.details || {}, null, 2)}</pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
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

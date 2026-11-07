import React from "react";

export const StatusBadge = ({ status, type = "order" }) => {
  const getStyles = () => {
    switch (status) {
      case "PENDING":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "CONFIRMED":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "PREPARING":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "READY_FOR_PICKUP":
        return "bg-indigo-100 text-indigo-800 border-indigo-200";
      case "OUT_FOR_DELIVERY":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "DELIVERED":
      case "SUCCESS":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "CANCELLED":
      case "FAILED":
      case "PAYMENT_FAILED":
        return "bg-rose-100 text-rose-800 border-rose-200";
      default:
        return "bg-stone-100 text-stone-800 border-stone-200";
    }
  };

  const formatText = (text) => {
    if (!text) return "";
    return text.replace(/_/g, " ");
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide border uppercase ${getStyles()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80 animate-pulse"></span>
      {formatText(status)}
    </span>
  );
};

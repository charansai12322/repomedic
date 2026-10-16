"use client";

import React, { ReactNode } from "react";
import { Breadcrumbs, BreadcrumbItem } from "./Breadcrumbs";

export interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  breadcrumbs,
  actions,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#21262D]">
      <div className="space-y-1 max-w-3xl">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <div className="mb-2">
            <Breadcrumbs items={breadcrumbs} />
          </div>
        )}
        {eyebrow && (
          <div className="inline-block text-[10px] font-mono uppercase tracking-widest text-[#8B949E] font-semibold">
            {eyebrow}
          </div>
        )}
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#E6EDF3]">
          {title}
        </h1>
        {description && (
          <p className="text-xs sm:text-sm text-[#8B949E] leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2.5 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}

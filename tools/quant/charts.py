"""
Chart Generator Tool
Generates financial charts using Plotly and exports as PNG/HTML.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import ClassVar

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class ChartInput(BaseModel):
    data: str = Field(description="JSON com dados para o gráfico")
    chart_type: str = Field(
        description=(
            "Tipo de gráfico: 'revenue_ebitda_bridge', 'waterfall', 'football_field', "
            "'debt_waterfall', 'margin_evolution', 'sensitivity_heatmap', 'comps_scatter'"
        )
    )
    title: str = Field(default="", description="Título do gráfico")
    output_path: str = Field(default="", description="Caminho para salvar (PNG). Vazio = retorna HTML inline.")
    company_name: str = Field(default="Target", description="Nome da empresa para labels")


class ChartGeneratorTool(BaseTool):
    name: str = "chart_generator"
    description: str = (
        "Gera gráficos financeiros profissionais (bridge, waterfall, football field, heatmap) "
        "usando Plotly. Retorna HTML inline ou salva PNG no caminho especificado."
    )
    args_schema: type[BaseModel] = ChartInput

    # IB-style color palette
    COLORS: ClassVar[dict] = {
        "primary": "#003366",
        "secondary": "#CC9900",
        "positive": "#006633",
        "negative": "#CC0000",
        "neutral": "#666666",
        "light_blue": "#4472C4",
        "light_green": "#70AD47",
        "light_red": "#FF0000",
        "gray": "#D9D9D9",
    }

    def _run(
        self,
        data: str,
        chart_type: str,
        title: str = "",
        output_path: str = "",
        company_name: str = "Target",
    ) -> str:
        try:
            import plotly.graph_objects as go
            import plotly.io as pio

            chart_data = json.loads(data)
            fig = None

            if chart_type == "revenue_ebitda_bridge":
                fig = self._revenue_ebitda_bridge(chart_data, title or f"{company_name} — Receita & EBITDA")
            elif chart_type == "waterfall":
                fig = self._waterfall_chart(chart_data, title or f"{company_name} — Waterfall")
            elif chart_type == "football_field":
                fig = self._football_field(chart_data, title or f"{company_name} — Football Field de Valuation")
            elif chart_type == "debt_waterfall":
                fig = self._debt_waterfall(chart_data, title or f"{company_name} — Estrutura de Dívida")
            elif chart_type == "margin_evolution":
                fig = self._margin_evolution(chart_data, title or f"{company_name} — Evolução de Margens")
            elif chart_type == "sensitivity_heatmap":
                fig = self._sensitivity_heatmap(chart_data, title or f"{company_name} — Sensibilidade EV")
            elif chart_type == "comps_scatter":
                fig = self._comps_scatter(chart_data, title or f"{company_name} — Posicionamento vs. Peers", company_name)
            else:
                return json.dumps({"error": f"chart_type '{chart_type}' não reconhecido."})

            if not fig:
                return json.dumps({"error": "Figura não gerada."})

            fig = self._apply_ib_theme(fig)

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                if output_path.endswith(".png"):
                    fig.write_image(str(path))
                else:
                    fig.write_html(str(path))
                return json.dumps({"saved": True, "path": str(path)})
            else:
                html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
                return json.dumps({"html": html[:2000] + "...[truncated]", "chart_type": chart_type})

        except Exception as exc:
            logger.error(f"Erro ao gerar gráfico: {exc}")
            return json.dumps({"error": str(exc)})

    def _revenue_ebitda_bridge(self, data: dict, title: str):
        import plotly.graph_objects as go

        years = data.get("years", [])
        revenues = data.get("revenues", [])
        ebitdas = data.get("ebitdas", [])
        margins = [e / r * 100 if r else 0 for e, r in zip(ebitdas, revenues)]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Receita Líquida", x=years, y=revenues,
            marker_color=self.COLORS["primary"], opacity=0.85,
        ))
        fig.add_trace(go.Bar(
            name="EBITDA", x=years, y=ebitdas,
            marker_color=self.COLORS["secondary"],
        ))
        fig.add_trace(go.Scatter(
            name="Margem EBITDA (%)", x=years, y=margins,
            mode="lines+markers+text", yaxis="y2",
            text=[f"{m:.1f}%" for m in margins],
            textposition="top center",
            line=dict(color=self.COLORS["positive"], width=2),
            marker=dict(size=8),
        ))
        fig.update_layout(
            title=title, barmode="overlay",
            yaxis=dict(title="R$ mil"),
            yaxis2=dict(title="Margem (%)", overlaying="y", side="right", showgrid=False),
        )
        return fig

    def _football_field(self, data: dict, title: str):
        import plotly.graph_objects as go

        methods = [m["method"] for m in data]
        lows = [m["low"] for m in data]
        highs = [m["high"] for m in data]
        mids = [m.get("mid") for m in data]

        fig = go.Figure()
        for i, (method, low, high, mid) in enumerate(zip(methods, lows, highs, mids)):
            color = [self.COLORS["primary"], self.COLORS["secondary"], self.COLORS["light_blue"]][i % 3]
            fig.add_trace(go.Bar(
                name=method,
                y=[method],
                x=[high - low],
                base=[low],
                orientation="h",
                marker_color=color,
                opacity=0.75,
            ))
            if mid:
                fig.add_trace(go.Scatter(
                    y=[method], x=[mid], mode="markers",
                    marker=dict(color="white", size=12, symbol="diamond", line=dict(width=2, color=color)),
                    showlegend=False,
                ))

        fig.update_layout(
            title=title,
            xaxis=dict(title="Enterprise Value (R$)"),
            barmode="stack",
        )
        return fig

    def _waterfall_chart(self, data: dict, title: str):
        import plotly.graph_objects as go

        labels = data.get("labels", [])
        values = data.get("values", [])
        measure = data.get("measure", ["relative"] * len(labels))

        fig = go.Figure(go.Waterfall(
            name="", orientation="v",
            measure=measure,
            x=labels,
            y=values,
            connector={"line": {"color": self.COLORS["neutral"]}},
            increasing={"marker": {"color": self.COLORS["positive"]}},
            decreasing={"marker": {"color": self.COLORS["negative"]}},
            totals={"marker": {"color": self.COLORS["primary"]}},
        ))
        fig.update_layout(title=title, showlegend=False)
        return fig

    def _margin_evolution(self, data: dict, title: str):
        import plotly.graph_objects as go

        years = data.get("years", [])
        fig = go.Figure()
        margin_types = {
            "gross_margin": ("Margem Bruta", self.COLORS["light_green"]),
            "ebitda_margin": ("Margem EBITDA", self.COLORS["primary"]),
            "net_margin": ("Margem Líquida", self.COLORS["secondary"]),
        }
        for key, (label, color) in margin_types.items():
            if key in data:
                vals = [v * 100 for v in data[key]]
                fig.add_trace(go.Scatter(
                    name=label, x=years, y=vals,
                    mode="lines+markers+text",
                    text=[f"{v:.1f}%" for v in vals],
                    textposition="top center",
                    line=dict(color=color, width=2),
                ))
        fig.update_layout(title=title, yaxis=dict(title="Margem (%)"))
        return fig

    def _sensitivity_heatmap(self, data: dict, title: str):
        import plotly.graph_objects as go

        z_vals = []
        x_labels = []
        y_labels = []

        for g_label, wacc_row in data.items():
            if not y_labels:
                x_labels = list(wacc_row.keys())
            y_labels.append(g_label)
            z_vals.append(list(wacc_row.values()))

        fig = go.Figure(go.Heatmap(
            z=z_vals, x=x_labels, y=y_labels,
            colorscale=[[0, self.COLORS["negative"]], [0.5, self.COLORS["gray"]], [1, self.COLORS["positive"]]],
            text=[[f"R${v:,.0f}" for v in row] for row in z_vals],
            texttemplate="%{text}",
        ))
        fig.update_layout(title=title, xaxis_title="WACC", yaxis_title="Taxa de crescimento (g)")
        return fig

    def _comps_scatter(self, data: dict, title: str, company_name: str):
        import plotly.graph_objects as go

        comps = data.get("comps", [])
        target = data.get("target", {})

        fig = go.Figure()
        if comps:
            fig.add_trace(go.Scatter(
                x=[c.get("ev_ebitda") for c in comps],
                y=[c.get("ebitda_margin", 0) * 100 for c in comps],
                mode="markers+text",
                text=[c.get("name", c.get("ticker", "")) for c in comps],
                textposition="top center",
                marker=dict(size=10, color=self.COLORS["primary"]),
                name="Peers",
            ))
        if target:
            fig.add_trace(go.Scatter(
                x=[target.get("ev_ebitda")],
                y=[target.get("ebitda_margin", 0) * 100],
                mode="markers+text",
                text=[company_name],
                textposition="top center",
                marker=dict(size=14, color=self.COLORS["secondary"], symbol="star"),
                name=company_name,
            ))
        fig.update_layout(
            title=title,
            xaxis_title="EV/EBITDA (x)",
            yaxis_title="Margem EBITDA (%)",
        )
        return fig

    def _debt_waterfall(self, data: dict, title: str):
        return self._waterfall_chart(data, title)

    def _apply_ib_theme(self, fig):
        fig.update_layout(
            font=dict(family="Arial", size=11, color="#333333"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=60, t=80, b=60),
        )
        fig.update_xaxes(showgrid=True, gridcolor="#E5E5E5", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="#E5E5E5", zeroline=False)
        return fig

import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const names = [
  "2020-Scrum-Guide-Spanish-Latin-South-American.pdf",
  "scrum_manager_historias_usuario.pdf",
  "Essential-Kanban-Condensed-Spanish.pdf",
  "Filosofia_Lean.pdf",
];
// open() solo funciona acá, en el contexto de inicio
const pdfs = names.map((n) => ({ name: n, data: open(`./pdfs/${n}`, "b") }));

export const options = {
  stages: [
    { duration: "10s", target: 100 },
    { duration: "20s", target: 100 },
    { duration: "10s", target: 0 },
  ],
};

export default function () {
  const pdf = pdfs[Math.floor(Math.random() * pdfs.length)];
  // NO setear Content-Type a mano: k6 agrega el boundary solo
  const res = http.post(`${BASE_URL}/extract`, {
    file: http.file(pdf.data, pdf.name, "application/pdf"),
  });
  check(res, {
    "status 200": (r) => r.status === 200,
    "tiene content y page_count": (r) => {
      try {
        const b = r.json();
        return typeof b.content === "string" && Number.isInteger(b.page_count);
      } catch (e) {
        return false;
      }
    },
  });
}

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const extraction_duration = new Trend("extraction_duration");

export const options = {
    stages: [
        { duration: "10s", VUs: 100 },
        { duration: "20s", VUs: 100 },
        { duration: "10s", VUs: 0 },
    ],
    thresholds: {
        http_req_failed: ["rate<0.01"],
        extraction_duration: ["p95<500ms"],
    },
};

const pdf_path = "./prueba.pdf";
const pdf_base64 = open(pdf_path, "b").base64.encode();

export default function () {
    const formData = {
        file: pdf_base64,
    };

    const params = {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    };

    const res = http.post(
        "http://localhost:8080/api/v1/extract",
        formData,
        params,
    );

    check(res, {
        "status 200": (r) => r.status === 200,
        "content is markdown": (r) => {
            const body = r.json();
            return body.content && body.page_count !== undefined;
        }),
    });

    sleep(1);
}
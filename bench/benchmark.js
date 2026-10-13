import http from 'k6/http';
import { check } from 'k6';

export const options = {
  discardResponseBodies: true,

  scenarios: {
    load_test: {
      executor: 'ramping-arrival-rate',

      // Start at 500 requests/iterations per second.
      startRate: 500,
      timeUnit: '1s',

      // Increase the offered load progressively.
      stages: [
        { duration: '30s', target: 1000 },
        { duration: '30s', target: 1500 },
        { duration: '30s', target: 2000 },
        { duration: '30s', target: 2500 },
        { duration: '30s', target: 3000 },
        { duration: '30s', target: 3500 },
        { duration: '30s', target: 4000 },
      ],

      preAllocatedVUs: 500,
      maxVUs: 2000,
      gracefulStop: '10s',
    },
  },

  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.999'],
    dropped_iterations: ['count==0'],
  },
};

export default function () {
  const res = http.get(__ENV.TARGET_URL, {
    timeout: '10s',
    tags: {
      proxy: __ENV.PROXY || 'unknown',
    },
  });

  check(res, {
    'status 200': (r) => r.status === 200,
  });
}


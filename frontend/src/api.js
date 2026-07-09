// Re-export the canonical API client so pages importing from '../../api'
// use the same configured axios instance as the services layer.
export { default, authAPI } from './services/api';

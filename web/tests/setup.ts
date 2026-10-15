import {afterEach, vi} from 'vitest';
import {cleanup} from '@testing-library/react';

Object.defineProperty(window, 'matchMedia', {value: vi.fn(() => ({
  matches: true, addEventListener() {}, removeEventListener() {},
}))});
window.scrollTo = vi.fn();
Object.defineProperty(window, 'ResizeObserver', {value: class {
  observe() {}
  unobserve() {}
  disconnect() {}
}});
Element.prototype.scrollIntoView = vi.fn();
Element.prototype.hasPointerCapture = () => false;
Element.prototype.releasePointerCapture = () => {};

afterEach(() => {cleanup(); vi.unstubAllGlobals(); history.replaceState({}, '', '/');});

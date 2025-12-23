# φ-Frame v1.0 — Static Boundary Shell

## Overview

The φ-Frame v1.0 is a **static boundary shell** designed with strict constraints to ensure deterministic, symbolic-only representation with no runtime behavior.

## Constraints

- **static-only**: No dynamic behavior or runtime execution
- **symbolic**: Purely representational and descriptive
- **no-light**: No lighting calculations or visual effects
- **no-math**: No mathematical computations
- **no-runtime**: No side effects or execution at import time
- **IP-shield strict**: Protected intellectual property boundaries

## Components

### 1. `index.js`

A pure static export containing the φ-Frame v1.0 specification. This module:
- Exports a plain object describing the boundary shell structure
- Has no side effects (no I/O, no Date, no randomness, no DOM)
- Contains no imports or external dependencies
- Provides symbolic layer definitions (shell, frame, field)

### 2. `diagram.svg`

A static SVG diagram representing the φ-Frame boundary shell concept:
- Concentric boundary rings showing the shell layers
- Central frame anchor with labeled components
- Text annotations for constraints and specifications
- No external references, scripts, or animations
- Valid, minimal SVG using neutral grayscale palette

### 3. `README.md`

This documentation file describing the φ-Frame v1.0 static boundary shell.

## Usage

To import the φ-Frame specification in your code:

```javascript
import { phiFrame } from './site/phi-frame/index.js';

console.log(phiFrame.name);      // "φ-Frame v1.0"
console.log(phiFrame.boundary);  // "static-light-boundary-shell"
console.log(phiFrame.layers);    // Array of layer definitions
```

Or use the default export:

```javascript
import phiFrame from './site/phi-frame/index.js';
```

## Scope

The φ-Frame v1.0 is limited to static, symbolic representation only. It does not include:
- Runtime behavior or execution logic
- Dynamic calculations or transformations
- Visual rendering or lighting effects
- External integrations or API calls

This is a foundational boundary definition for the phi-cosmography architecture.

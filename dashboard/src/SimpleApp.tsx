import React from 'react';

// UNCOMMENT NOTHING. PURE TEST.

export default function SimpleApp() {
    console.log("SimpleApp Rendering. PURE.");
    return (
        <div style={{ padding: 50, background: 'orange' }}>
            <h1>SIMPLE APP WORKING</h1>
            <p>If you see this, React is alive.</p>
        </div>
    );
}

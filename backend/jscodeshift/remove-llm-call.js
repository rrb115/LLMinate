module.exports = function transformer(file, api) {
  const j = api.jscodeshift;
  const root = j(file.source);

  root.find(j.CallExpression)
    .filter(path => {
      const callee = path.node.callee;
      return (
        callee &&
        callee.type === 'MemberExpression' &&
        callee.property &&
        ['generate', 'complete', 'create', 'generateContent'].includes(callee.property.name)
      );
    })
    .replaceWith(() => j.identifier('/* deterministic replacement placeholder */ null'));

  return root.toSource();
};

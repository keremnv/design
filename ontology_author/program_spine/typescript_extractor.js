#!/usr/bin/env node

/*
 * Small TypeScript Compiler API adapter.
 *
 * This process emits extraction facts and evidence descriptors.  It does not
 * emit World rows and it does not make TypeScript AST types part of the
 * program-spine contract.  The Python side owns IDs, grounding, World
 * projection, admission, and publication.
 */

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

function loadTypeScript() {
  const candidates = [];
  if (process.env.TYPESCRIPT_PATH) candidates.push(process.env.TYPESCRIPT_PATH);
  candidates.push(path.resolve(__dirname, "../../frontend/node_modules/typescript"));
  candidates.push("typescript");
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (_error) {
      // Try the next installation location.
    }
  }
  throw new Error(
    "TypeScript is unavailable; install the repository frontend dependencies " +
      "or set TYPESCRIPT_PATH"
  );
}

const ts = loadTypeScript();

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function canonicalPath(fileName) {
  const resolved = path.resolve(fileName);
  return ts.sys.useCaseSensitiveFileNames ? resolved : resolved.toLowerCase();
}

function under(fileName, root) {
  const file = canonicalPath(fileName);
  const base = canonicalPath(root);
  return file === base || file.startsWith(base.endsWith(path.sep) ? base : base + path.sep);
}

function isTestFile(fileName) {
  const normalized = canonicalPath(fileName).split(path.sep).join("/");
  return (
    normalized.includes("/__tests__/") ||
    normalized.includes("/tests/") ||
    normalized.includes("/test/") ||
    /\.(test|spec)\.[^.]+$/.test(normalized)
  );
}

function isGeneratedFile(fileName) {
  const normalized = canonicalPath(fileName).split(path.sep).join("/");
  return (
    normalized.includes("/generated/") ||
    normalized.includes("/dist/") ||
    normalized.includes("/build/") ||
    normalized.endsWith(".generated.ts") ||
    normalized.endsWith(".generated.tsx")
  );
}

function isNodeModule(fileName) {
  return canonicalPath(fileName).split(path.sep).join("/").includes("/node_modules/");
}

function isTypeScriptLibrary(fileName) {
  const normalized = canonicalPath(fileName).split(path.sep).join("/");
  return normalized.includes("/typescript/lib/") || /^lib\.[^/]+\.d\.ts$/.test(path.basename(normalized));
}

function classify(fileName, boundary) {
  const workspaceRoots = boundary.workspace_roots || [];
  const packageRoots = boundary.package_roots || workspaceRoots;
  const insidePackage = packageRoots.some((root) => under(fileName, root));
  const insideWorkspace = workspaceRoots.some((root) => under(fileName, root));
  if (isNodeModule(fileName) || isTypeScriptLibrary(fileName)) return "ANALYSIS_SUPPORT";
  if (!insidePackage) return insideWorkspace ? "EXTERNAL_BOUNDARY" : "ANALYSIS_SUPPORT";
  if (boundary.include_tests === false && isTestFile(fileName)) return "ANALYSIS_SUPPORT";
  if (boundary.generated_files === "exclude" && isGeneratedFile(fileName)) {
    return "ANALYSIS_SUPPORT";
  }
  return "IN_SCOPE";
}

function inputRecord(fileName, disposition) {
  const resolved = path.resolve(fileName);
  let bytes = null;
  try {
    bytes = fs.readFileSync(resolved);
  } catch (_error) {
    const text = ts.sys.readFile(resolved);
    if (text !== undefined) bytes = Buffer.from(text, "utf8");
  }
  return {
    path: resolved,
    disposition,
    contentDigest: bytes ? sha256(bytes) : null,
    byteLength: bytes ? bytes.length : null,
    readable: Boolean(bytes),
  };
}

function packageInfo(fileName) {
  const normalized = path.resolve(fileName).split(path.sep);
  const nodeModulesIndex = normalized.lastIndexOf("node_modules");
  if (nodeModulesIndex < 0 || nodeModulesIndex + 1 >= normalized.length) return null;
  const packageParts = normalized[nodeModulesIndex + 1].startsWith("@")
    ? normalized.slice(nodeModulesIndex + 1, nodeModulesIndex + 3)
    : normalized.slice(nodeModulesIndex + 1, nodeModulesIndex + 2);
  const absoluteRoot = path.parse(path.resolve(fileName)).root;
  const packageRoot = path.join(absoluteRoot, ...normalized.slice(1, nodeModulesIndex + 1), ...packageParts);
  const packageJsonPath = path.join(packageRoot, "package.json");
  let metadata = {};
  try {
    metadata = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
  } catch (_error) {
    // A declaration can be resolved even when package metadata is unavailable.
  }
  const relativeFile = path.relative(packageRoot, path.resolve(fileName)).split(path.sep).join("/");
  return {
    name: metadata.name || packageParts.join("/"),
    version: metadata.version || "unknown",
    packageRoot,
    packageJson: inputRecord(packageJsonPath, "ANALYSIS_SUPPORT"),
    relativeFile,
  };
}

function range(sourceFile, node) {
  return {
    file: path.resolve(sourceFile.fileName),
    start: node.getStart(sourceFile),
    end: node.end,
  };
}

function declarationName(node) {
  if (node.name && ts.isIdentifier(node.name)) return node.name.text;
  if (node.name && ts.isStringLiteral(node.name)) return node.name.text;
  return "";
}

function loadRequest() {
  const input = fs.readFileSync(0, "utf8");
  return JSON.parse(input);
}

function extendedConfigPath(configPath, value) {
  const text = String(value);
  const candidate = path.isAbsolute(text) ? text : path.resolve(path.dirname(configPath), text);
  if (ts.sys.fileExists(candidate)) return candidate;
  if (ts.sys.fileExists(`${candidate}.json`)) return `${candidate}.json`;
  return null;
}

function configurationChain(configPath, seen = new Set()) {
  const resolved = path.resolve(configPath);
  if (seen.has(resolved)) return [];
  seen.add(resolved);
  const output = [inputRecord(resolved, "ANALYSIS_SUPPORT")];
  const read = ts.readConfigFile(resolved, ts.sys.readFile);
  const extendsValue = read && read.config && read.config.extends;
  const values = Array.isArray(extendsValue) ? extendsValue : extendsValue ? [extendsValue] : [];
  for (const value of values) {
    const parent = extendedConfigPath(resolved, value);
    if (parent) output.push(...configurationChain(parent, seen));
  }
  return output;
}

function extract(request) {
  const boundary = request.boundary || {};
  const projectPaths = (boundary.projects || []).map((item) =>
    path.resolve(typeof item === "string" ? item : item.tsconfig)
  );
  if (!projectPaths.length) throw new Error("at least one TypeScript project is required");

  const configDiagnostics = [];
  const parsedProjects = [];
  const configurationInputs = [];
  const configurationSeen = new Set();
  const parseHost = {
    useCaseSensitiveFileNames: ts.sys.useCaseSensitiveFileNames,
    fileExists: ts.sys.fileExists,
    readFile: ts.sys.readFile,
    readDirectory: ts.sys.readDirectory,
    getCurrentDirectory: ts.sys.getCurrentDirectory,
    onUnRecoverableConfigFileDiagnostic: (diagnostic) => configDiagnostics.push(diagnostic),
  };
  for (const configPath of projectPaths) {
    const parsed = ts.getParsedCommandLineOfConfigFile(configPath, {}, parseHost);
    if (!parsed) throw new Error(`could not parse TypeScript configuration ${configPath}`);
    parsedProjects.push({ configPath, parsed });
    configDiagnostics.push(...(parsed.errors || []));
    for (const input of configurationChain(configPath, configurationSeen)) configurationInputs.push(input);
  }

  const allRootNames = [...new Set(parsedProjects.flatMap((item) => item.parsed.fileNames))];
  const options = parsedProjects[0].parsed.options;
  const projectReferences = parsedProjects.flatMap((item) => item.parsed.projectReferences || []);
  const program = ts.createProgram({
    rootNames: allRootNames,
    options,
    projectReferences,
  });
  const checker = program.getTypeChecker();
  const sourceFiles = program.getSourceFiles();
  const projectForFile = new Map();
  for (const item of parsedProjects) {
    for (const fileName of item.parsed.fileNames) projectForFile.set(canonicalPath(fileName), item.configPath);
  }

  const files = sourceFiles.map((sourceFile) => {
    const disposition = classify(sourceFile.fileName, boundary);
    return {
      ...inputRecord(sourceFile.fileName, disposition),
      isDeclarationFile: Boolean(sourceFile.isDeclarationFile),
      language: ts.ScriptKind[sourceFile.scriptKind] || "Unknown",
      project: projectForFile.get(canonicalPath(sourceFile.fileName)) || projectPaths[0],
      moduleKey: `module|${canonicalPath(sourceFile.fileName)}|${projectForFile.get(canonicalPath(sourceFile.fileName)) || projectPaths[0]}`,
      analyzed: disposition === "IN_SCOPE",
    };
  });
  const fileByPath = new Map(files.map((file) => [canonicalPath(file.path), file]));
  const elements = [];
  const ownership = [];
  const imports = [];
  const calls = [];
  const typeRelations = [];
  const resolutions = [];
  const dependencyResolutions = [];
  const elementByDescriptor = new Map();
  const ordinalByOwner = new Map();

  function nextOrdinal(owner, category) {
    const key = `${owner}|${category}`;
    const value = ordinalByOwner.get(key) || 0;
    ordinalByOwner.set(key, value + 1);
    return value;
  }

  function symbolKey(symbol) {
    if (!symbol) return null;
    try {
      if (symbol.flags & ts.SymbolFlags.Alias) symbol = checker.getAliasedSymbol(symbol);
      return checker.getFullyQualifiedName(symbol);
    } catch (_error) {
      return null;
    }
  }

  function symbolForNode(node) {
    if (!node) return null;
    const nameNode = node.name && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name))
      ? node.name
      : node;
    return symbolKey(checker.getSymbolAtLocation(nameNode));
  }

  function kindForDeclaration(node) {
    if (ts.isClassDeclaration(node) || ts.isClassExpression(node)) return ["class", "ClassUnit"];
    if (ts.isInterfaceDeclaration(node)) return ["interface", "InterfaceUnit"];
    if (ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node) || ts.isArrowFunction(node)) {
      return ["function", "CallableUnit"];
    }
    if (ts.isMethodDeclaration(node) || ts.isMethodSignature(node) || ts.isConstructorDeclaration(node) ||
        ts.isGetAccessorDeclaration(node) || ts.isSetAccessorDeclaration(node)) {
      return ["method", "MethodUnit"];
    }
    if (ts.isPropertyDeclaration(node) || ts.isPropertySignature(node)) return ["field", "MemberUnit"];
    if (ts.isParameter(node)) return ["data", "ParameterUnit"];
    if (ts.isVariableDeclaration(node)) return ["data", "StorableUnit"];
    return null;
  }

  function addElement({ descriptor, programKind, kdmKind, node, sourceFile, owner, synthetic = false, name = "" }) {
    const existing = elementByDescriptor.get(descriptor);
    const item = {
      descriptor,
      programKind,
      kdmKind,
      synthetic,
      name,
      ownerDescriptor: owner || null,
      evidence: node ? [range(sourceFile, node)] : [],
    };
    if (existing) {
      existing.evidence.push(...item.evidence);
      if (!existing.ownerDescriptor && item.ownerDescriptor) existing.ownerDescriptor = item.ownerDescriptor;
      return existing;
    }
    elementByDescriptor.set(descriptor, item);
    elements.push(item);
    if (owner && owner !== descriptor) ownership.push({ from: owner, to: descriptor, evidence: item.evidence[0] || null });
    return item;
  }

  function isCallableDeclaration(node) {
    return Boolean(
      node && (
        ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node) ||
        ts.isArrowFunction(node) || ts.isMethodDeclaration(node) ||
        ts.isMethodSignature(node) || ts.isConstructorDeclaration(node) ||
        ts.isGetAccessorDeclaration(node) || ts.isSetAccessorDeclaration(node)
      )
    );
  }

  function signatureKey(node, fallback) {
    try {
      const signature = checker.getSignatureFromDeclaration(node);
      if (signature) {
        return checker.signatureToString(
          signature,
          node,
          ts.TypeFormatFlags.NoTruncation | ts.TypeFormatFlags.UseAliasDefinedOutsideCurrentScope
        );
      }
    } catch (_error) {
      // Some incomplete declarations have no checker signature. The
      // declaration ordinal is still a deterministic snapshot-local fallback.
    }
    return fallback;
  }

  function addSignatures(parent, node, sourceFile) {
    const symbol = symbolForNode(node);
    const declarations = symbol
      ? (checker.getSymbolAtLocation(node.name || node)?.declarations || []).filter(isCallableDeclaration)
      : [node];
    const candidates = declarations.length ? declarations : [node];
    const seen = new Set();
    candidates.forEach((declaration, index) => {
      const declarationFile = declaration.getSourceFile();
      const key = signatureKey(declaration, `ordinal:${index}`);
      const descriptor = `element|${moduleDescriptor(declarationFile)}|Signature|${symbol || parent.descriptor}|${key}`;
      if (seen.has(descriptor)) return;
      seen.add(descriptor);
      addElement({
        descriptor,
        programKind: "signature",
        kdmKind: "Signature",
        node: declaration,
        sourceFile: declarationFile,
        owner: parent.descriptor,
        synthetic: false,
        name: "signature",
      });
    });
  }

  function containsDirectCall(node) {
    let found = false;
    function scan(child) {
      if (found) return;
      if (ts.isCallExpression(child) || ts.isNewExpression(child)) {
        found = true;
        return;
      }
      if (child !== node && isCallableDeclaration(child)) return;
      ts.forEachChild(child, scan);
    }
    ts.forEachChild(node, scan);
    return found;
  }

  function moduleDescriptor(sourceFile) {
    const file = fileByPath.get(canonicalPath(sourceFile.fileName));
    return file ? file.moduleKey : `module|${canonicalPath(sourceFile.fileName)}|${projectPaths[0]}`;
  }

  function declarationDescriptor(sourceFile, node, kdmKind, owner, symbol, name) {
    const stableSymbol = symbol || `anonymous|${owner}|${kdmKind}|${nextOrdinal(owner, "declaration")}`;
    return `element|${moduleDescriptor(sourceFile)}|${kdmKind}|${stableSymbol}`;
  }

  function targetFromDeclaration(declaration) {
    if (!declaration) return null;
    const sourceFile = declaration.getSourceFile();
    const pair = kindForDeclaration(declaration);
    let symbol = symbolForNode(declaration);
    let programKind = pair ? pair[0] : "module";
    let kdmKind = pair ? pair[1] : "CodeItem";
    let owner = moduleDescriptor(sourceFile);
    if (ts.isConstructorDeclaration(declaration)) {
      const classTarget = targetFromDeclaration(declaration.parent);
      if (classTarget) {
        symbol = `constructor|${classTarget.symbol}`;
        owner = classTarget.descriptor;
      }
    }
    if (ts.isVariableDeclaration(declaration) && declaration.initializer &&
        (ts.isArrowFunction(declaration.initializer) || ts.isFunctionExpression(declaration.initializer))) {
      programKind = "function";
      kdmKind = "CallableUnit";
      symbol = symbol || symbolForNode(declaration);
    }
    if (!symbol) return null;
    const sourceRecord = fileByPath.get(canonicalPath(sourceFile.fileName));
    const external = sourceRecord && sourceRecord.disposition !== "IN_SCOPE";
    const packageIdentity = external && packageInfo(sourceFile.fileName);
    const descriptor = external
      ? `external|${packageIdentity ? `${packageIdentity.name}@${packageIdentity.version}|${packageIdentity.relativeFile}` : canonicalPath(sourceFile.fileName)}|${kdmKind}|${symbol}`
      : `element|${moduleDescriptor(sourceFile)}|${kdmKind}|${symbol}`;
    return { descriptor, programKind, kdmKind, symbol, file: sourceFile.fileName, declaration, owner };
  }

  function typeTarget(typeNode) {
    if (!typeNode) return null;
    const symbol = symbolKey(checker.getSymbolAtLocation(typeNode));
    if (!symbol) return null;
    const declarations = checker.getSymbolAtLocation(typeNode)?.declarations || [];
    const target = targetFromDeclaration(declarations[0]);
    if (target) return target;
    return { descriptor: `external|type|${symbol}`, programKind: "type", kdmKind: "Datatype", symbol, file: null, declaration: null };
  }

  function targetForCall(expression, callNode) {
    const candidates = [];
    if (ts.isPropertyAccessExpression(expression)) {
      const receiver = checker.getTypeAtLocation(expression.expression);
      const types = receiver && receiver.isUnion() ? receiver.types : [receiver];
      for (const candidateType of types || []) {
        const property = candidateType && candidateType.getProperty(expression.name.text);
        const target = property && targetFromDeclaration(property.valueDeclaration || (property.declarations || [])[0]);
        if (target && !candidates.some((item) => item.descriptor === target.descriptor)) candidates.push(target);
      }
      if (candidates.length > 1) return candidates;
    }
    const signature = checker.getResolvedSignature(callNode);
    if (signature && signature.declaration) {
      let target = targetFromDeclaration(signature.declaration);
      if (ts.isNewExpression(callNode) && target && target.kdmKind === "ClassUnit") {
        const constructorDescriptor = `element|${moduleDescriptor(target.declaration.getSourceFile())}|MethodUnit|constructor|${target.symbol}`;
        const constructor = addElement({
          descriptor: constructorDescriptor,
          programKind: "method",
          kdmKind: "MethodUnit",
          node: target.declaration,
          sourceFile: target.declaration.getSourceFile(),
          owner: target.descriptor,
          synthetic: true,
          name: "constructor",
        });
        target = {
          ...target,
          descriptor: constructor.descriptor,
          programKind: "method",
          kdmKind: "MethodUnit",
        };
      }
      if (target) candidates.push(target);
    }
    const type = checker.getTypeAtLocation(expression);
    if (!candidates.length && type && !(type.flags & ts.TypeFlags.Any)) {
      const signatureKind = ts.isNewExpression(callNode) ? ts.SignatureKind.Construct : ts.SignatureKind.Call;
      for (const candidateSignature of checker.getSignaturesOfType(type, signatureKind)) {
        const target = targetFromDeclaration(candidateSignature.declaration);
        if (target && !candidates.some((item) => item.descriptor === target.descriptor)) candidates.push(target);
      }
    }
    if (!candidates.length && ts.isPropertyAccessExpression(expression)) {
      const receiver = checker.getTypeAtLocation(expression.expression);
      const types = receiver && receiver.isUnion() ? receiver.types : [receiver];
      for (const candidateType of types || []) {
        const property = candidateType && candidateType.getProperty(expression.name.text);
        const target = property && targetFromDeclaration(property.valueDeclaration || (property.declarations || [])[0]);
        if (target && !candidates.some((item) => item.descriptor === target.descriptor)) candidates.push(target);
      }
    }
    return candidates;
  }

  function moduleTarget(sourceFile, moduleSpecifier) {
    // Use the public resolver directly.  Program's internal redirect lookup
    // requires additional project-reference state that this small adapter
    // intentionally does not expose.
    const result = ts.resolveModuleName(
      moduleSpecifier.text,
      sourceFile.fileName,
      options,
      ts.sys
    );
    const resolved = result && result.resolvedModule;
    if (!resolved || !resolved.resolvedFileName) return null;
    const targetFile = fileByPath.get(canonicalPath(resolved.resolvedFileName));
    if (targetFile && targetFile.disposition === "IN_SCOPE") {
      return { descriptor: targetFile.moduleKey, file: targetFile.path, programKind: "module", kdmKind: "Module" };
    }
    return {
      descriptor: (() => {
        const packageIdentity = packageInfo(resolved.resolvedFileName);
        return packageIdentity
          ? `external|module|${packageIdentity.name}@${packageIdentity.version}|${packageIdentity.relativeFile}`
          : `external|module|${canonicalPath(resolved.resolvedFileName)}|${moduleSpecifier.text}`;
      })(),
      file: resolved.resolvedFileName,
      programKind: "module",
      kdmKind: "Module",
    };
  }

  function visit(sourceFile, node, owner) {
    let currentOwner = owner;
    const pair = kindForDeclaration(node);
    const name = declarationName(node);
    let declarationItem = null;
    if (pair) {
      let symbol = symbolForNode(node);
      if ((ts.isFunctionExpression(node) || ts.isArrowFunction(node)) &&
          ts.isVariableDeclaration(node.parent) && node.parent.initializer === node) {
        symbol = symbolForNode(node.parent) || symbol;
      }
      const assignedCallable =
        (ts.isFunctionExpression(node) || ts.isArrowFunction(node)) &&
        ts.isVariableDeclaration(node.parent) && node.parent.initializer === node &&
        Boolean(declarationName(node.parent));
      if ((ts.isFunctionExpression(node) || ts.isArrowFunction(node)) && !symbol &&
          !assignedCallable && !containsDirectCall(node)) {
        // An unused anonymous function has no required KDM identity in v0.
        // Its source range remains available through the containing element.
        ts.forEachChild(node, (child) => visit(sourceFile, child, currentOwner));
        return;
      }
      if (ts.isConstructorDeclaration(node) && !symbol) {
        symbol = `constructor|${symbolForNode(node.parent) || "anonymous-class"}`;
      }
      if ((ts.isFunctionExpression(node) || ts.isArrowFunction(node)) && !symbol) {
        symbol = `anonymous|${owner}|${pair[1]}|${nextOrdinal(owner, "callable")}`;
      }
      const descriptor = declarationDescriptor(sourceFile, node, pair[1], owner, symbol, name);
      const synthetic = ts.isFunctionExpression(node) || ts.isArrowFunction(node);
      declarationItem = addElement({
        descriptor,
        programKind: pair[0],
        kdmKind: pair[1],
        node,
        sourceFile,
        owner,
        synthetic,
        name,
      });
      currentOwner = descriptor;
      if (pair[1] === "CallableUnit" || pair[1] === "MethodUnit") {
        addSignatures(declarationItem, node, sourceFile);
      }
      if (ts.isVariableDeclaration(node) && node.initializer &&
          (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer))) {
        const callableDescriptor = `element|${moduleDescriptor(sourceFile)}|CallableUnit|${symbol || `anonymous|${descriptor}`}`;
        const callable = addElement({
          descriptor: callableDescriptor,
          programKind: "function",
          kdmKind: "CallableUnit",
          node: node.initializer,
          sourceFile,
          owner,
          synthetic: true,
          name,
        });
        addSignatures(callable, node.initializer, sourceFile);
        currentOwner = callableDescriptor;
      }
    }

    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
      const specifier = node.moduleSpecifier;
      if (specifier && ts.isStringLiteral(specifier)) {
        const target = moduleTarget(sourceFile, specifier);
        const subject = moduleDescriptor(sourceFile);
        const evidence = range(sourceFile, specifier);
        if (target) {
          imports.push({ from: subject, to: target.descriptor, evidence, specifier: specifier.text });
          const packageIdentity = target.file && packageInfo(target.file);
          if (packageIdentity) {
            dependencyResolutions.push({
              source: sourceFile.fileName,
              specifier: specifier.text,
              target: target.file,
              package: {
                name: packageIdentity.name,
                version: packageIdentity.version,
                packageJson: packageIdentity.packageJson,
              },
            });
          }
          resolutions.push({
            subject,
            relationName: "kdm_imports",
            status: "RESOLVED",
            evidence,
            candidates: [target.descriptor],
            details: { specifier: specifier.text, targetFile: target.file },
          });
        } else {
          resolutions.push({
            subject,
            relationName: "kdm_imports",
            status: "UNRESOLVED",
            evidence,
            candidates: [],
            details: { specifier: specifier.text, reason: "module resolution did not establish a target" },
          });
        }
      }
    }

    if (ts.isCallExpression(node) || ts.isNewExpression(node)) {
      const actionDescriptor = `element|${moduleDescriptor(sourceFile)}|ActionElement|${currentOwner}|${nextOrdinal(currentOwner, "action")}`;
      addElement({
        descriptor: actionDescriptor,
        programKind: "action",
        kdmKind: "ActionElement",
        node,
        sourceFile,
        owner: currentOwner,
        synthetic: true,
        name: ts.isNewExpression(node) ? "constructor_call" : "call",
      });
      const expression = node.expression;
      const candidates = targetForCall(expression, node);
      const evidence = range(sourceFile, node);
      const status = candidates.length === 1 ? "RESOLVED" : candidates.length > 1 ? "MULTIPLE_CANDIDATES" : "UNRESOLVED";
      const targetDescriptors = candidates.map((item) => item.descriptor);
      if (status === "RESOLVED") calls.push({ from: actionDescriptor, to: targetDescriptors[0], evidence, kind: ts.isNewExpression(node) ? "constructor" : "call" });
      resolutions.push({
        subject: actionDescriptor,
        relationName: "kdm_calls",
        status,
        evidence,
        candidates: targetDescriptors,
        details: {
          call_kind: ts.isNewExpression(node) ? "constructor" : "call",
          constructor: ts.isNewExpression(node),
          targetSymbols: candidates.map((item) => item.symbol || null),
          selectedSignature: (() => {
            try {
              const selected = checker.getResolvedSignature(node);
              return selected ? checker.signatureToString(selected, node, ts.TypeFormatFlags.NoTruncation) : null;
            } catch (_error) {
              return null;
            }
          })(),
          candidateSignatures: (() => {
            try {
              const type = checker.getTypeAtLocation(expression);
              const kind = ts.isNewExpression(node) ? ts.SignatureKind.Construct : ts.SignatureKind.Call;
              return checker.getSignaturesOfType(type, kind).map((item) =>
                checker.signatureToString(item, node, ts.TypeFormatFlags.NoTruncation)
              );
            } catch (_error) {
              return [];
            }
          })(),
        },
      });
    }

    if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node)) {
      for (const clause of node.heritageClauses || []) {
        for (const type of clause.types) {
          const target = typeTarget(type.expression);
          if (!target) continue;
          typeRelations.push({
            relationName: clause.token === ts.SyntaxKind.ImplementsKeyword ? "kdm_implements" : "kdm_extends",
            from: declarationItem ? declarationItem.descriptor : currentOwner,
            to: target.descriptor,
            evidence: range(sourceFile, type),
          });
        }
      }
    }

    if (ts.isPropertyDeclaration(node) || ts.isParameter(node) || ts.isVariableDeclaration(node)) {
      const target = typeTarget(node.type);
      if (target && declarationItem) {
        typeRelations.push({ relationName: "kdm_has_type", from: declarationItem.descriptor, to: target.descriptor, evidence: range(sourceFile, node.type) });
      }
    }

    ts.forEachChild(node, (child) => visit(sourceFile, child, currentOwner));
  }

  for (const sourceFile of sourceFiles) {
    const file = fileByPath.get(canonicalPath(sourceFile.fileName));
    if (!file || file.disposition !== "IN_SCOPE") continue;
    const module = addElement({
      descriptor: file.moduleKey,
      programKind: "module",
      kdmKind: "Module",
      node: sourceFile,
      sourceFile,
      owner: null,
      name: path.basename(sourceFile.fileName),
    });
    const compilation = addElement({
      descriptor: `element|${module.descriptor}|CompilationUnit`,
      programKind: "file",
      kdmKind: "CompilationUnit",
      node: sourceFile,
      sourceFile,
      owner: module.descriptor,
      name: path.basename(sourceFile.fileName),
    });
    ts.forEachChild(sourceFile, (child) => visit(sourceFile, child, compilation.descriptor));
  }

  return {
    tool: { name: "typescript-compiler-api", version: ts.version },
    projects: projectPaths,
    compilerOptions: options,
    configurationInputs,
    dependencyResolutions,
    configDiagnostics: configDiagnostics.map((diagnostic) => ({
      code: diagnostic.code,
      category: diagnostic.category,
      message: ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n"),
      file: diagnostic.file ? path.resolve(diagnostic.file.fileName) : null,
      start: diagnostic.start ?? null,
      length: diagnostic.length ?? null,
    })),
    programDiagnostics: ts.getPreEmitDiagnostics(program).map((diagnostic) => ({
      code: diagnostic.code,
      category: diagnostic.category,
      message: ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n"),
      file: diagnostic.file ? path.resolve(diagnostic.file.fileName) : null,
      start: diagnostic.start ?? null,
      length: diagnostic.length ?? null,
    })),
    files,
    elements,
    ownership,
    imports,
    calls,
    typeRelations,
    resolutions,
  };
}

try {
  const request = loadRequest();
  process.stdout.write(JSON.stringify(extract(request)));
} catch (error) {
  process.stderr.write(`${error && error.stack ? error.stack : error}\n`);
  process.exitCode = 1;
}

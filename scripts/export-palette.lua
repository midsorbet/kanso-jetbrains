-- Export kanso.nvim's palette and the resolved colors of each variant as JSON.
--
-- Usage: nvim --headless -u NONE -l scripts/export-palette.lua <kanso.nvim directory>
--
-- The theme roles (ui, syn, diag, diff, vcs, term) come from kanso.nvim itself, so
-- the JetBrains themes follow the same color decisions as the Neovim colorscheme.
local kanso_dir = assert(arg[1], 'usage: export-palette.lua <kanso.nvim directory>')
vim.opt.runtimepath:prepend(kanso_dir)

require('kanso').setup({})

local result = { themes = {} }
for _, name in ipairs({ 'zen', 'ink', 'mist', 'pearl' }) do
  vim.o.background = name == 'pearl' and 'light' or 'dark'
  package.loaded['kanso.colors'] = nil
  package.loaded['kanso.themes'] = nil
  local colors = require('kanso.colors').setup({ theme = name, foreground = 'default' })
  result.palette = colors.palette
  result.themes[name] = colors.theme
end

io.stdout:write(vim.json.encode(result), '\n')

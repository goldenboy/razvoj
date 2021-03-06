% if visible:
    % if icon:
        <a class="listImage-container" name="${name}" id="${name}" title="${help}" context="${ctx}" ${py.attrs(attrs)}
            onclick="new ListView('${parent_grid}').onButtonClick('${name}', '${btype}', ${id}, '${confirm}', getNodeAttribute(this, 'context'));">
            <img height="16" width="16" class="listImage" src="${icon}"/>
        </a>
    % else:
        <a class="button-b" name="${name}" id="${name}" href="javascript: void(0)" ${py.attrs(attrs, context=ctx)} title="${help}"
            onclick="new ListView('${parent_grid}').onButtonClick('${name}', '${btype}', ${id}, '${confirm}', getNodeAttribute(this, 'context'))">
            ${string}
        </a>
    % endif
% elif not icon:
    <span><img style="display:none" name="${name}" id="${name}" height="16" width="16" class="listImage" src="${icon}" title="${help}" context="${ctx}" ${py.attrs(attrs)} onclick="new ListView('${parent_grid}').onButtonClick('${name}', '${btype}', ${id}, '${confirm}', getNodeAttribute(this, 'context'))"/></span>
% endif

<%
    plus_icon = "https://github.com/openmicroscopy/openmicroscopy/diff_blob/55ef9e4acc887a5d2b13e62ffb1e766d608f6dbe/components/tools/OmeroWeb/omeroweb/webtest/media/img/panojs/16px_plus.png?raw=true"
    minus_icon = "https://github.com/openmicroscopy/openmicroscopy/diff_blob/55ef9e4acc887a5d2b13e62ffb1e766d608f6dbe/components/tools/OmeroWeb/omeroweb/webtest/media/img/panojs/16px_minus.png?raw=true"
    
    sorted_paths = sorted(documentation_dict.iterkeys())
    endpoint_order = ('description', 'required', 'optional', 'unlimited', 'returns')
%>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    
    <title>${documentation_title}</title>
    <style type="text/css">
        *, html { font-family: Verdana, Arial, Helvetica, sans-serif; }
        
        body, form, ul, li, p, h1, h2, h3, h4, h5
        {
            margin: 0;
            padding: 0;
        }
        body { background-color: #606061; color: #ffffff; margin: 0; }
        img { border: none; }
        p
        {
            font-size: 1em;
            margin: 0 0 1em 0;
        }
        
        html { font-size: 100%; /* IE hack */ }
        body { font-size: 1em; /* Sets base font size to 16px */ }
        table { font-size: 100%; /* IE hack */ }
        input, select, textarea, th, td { font-size: 1em; }
        
        /* CSS Tree menu styles */
        ol.tree
        {
            padding: 0 0 0 30px;
            width: 300px;
        }
            li
            {
                position: relative;
                margin-left: -15px;
                list-style: none;
            }
            li.item
            {
                margin-left: -1px !important;
            }
                li.item a
                {
                    color: #fff;
                    text-decoration: none;
                    display: block;
                }
            li input
            {
                position: absolute;
                left: 0;
                margin-left: 0;
                opacity: 0;
                z-index: 2;
                cursor: pointer;
                height: 1em;
                width: 1em;
                top: 0;
            }
                li input + ol
                {
                    background: url(${plus_icon}) 40px 0 no-repeat;
                    margin: -0.938em 0 0 -44px; /* 15px */
                    height: 1em;
                }
                li input + ol > li { display: none; margin-left: -14px !important; padding-left: 1px; }
            li label
            {
                cursor: pointer;
                display: block;
                padding-left: 18px;
            }
            
            li input:checked + ol
            {
                background: url(${minus_icon}) 40px 5px no-repeat;
                margin: -1.25em 0 0 -44px; /* 20px */
                padding: 1.563em 0 0 80px;
                height: auto;
            }
                li input:checked + ol > li { display: block; margin: 0 0 0.125em;  /* 2px */}
                li input:checked + ol > li:last-child { margin: 0 0 0.063em; /* 1px */ }
    </style>

</head>
<body>
    
    <ol class="tree">
        % for path, methods_dict in [(path, documentation_dict[path]) for path in sorted_paths]:
        <li>
            <label for="${path}">${path}</label> <input type="checkbox" id="${path}" />
            <ol>
                % for method, endpoint_dict in methods_dict.iteritems():
                <% path_method = '-'.join([path, method]) %>
                <li>
                    <label for="${path_method}">${method}</label> <input type="checkbox" id=${path_method} />
                    <ol>
                        % for name, value in [(ikey, endpoint_dict[ikey]) for ikey in endpoint_order if ikey in endpoint_dict]:
                        <% caption = name.capitalize() + ':' %>
                        <li class="item"><a>${caption}</a><a>${value}</a></li>
                        % endfor
                    </ol>
                </li>
                % endfor
            </ol>
        </li>
        % endfor
    </ol>
    
</body>
</html>








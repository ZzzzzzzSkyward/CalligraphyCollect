//异体字检索
async function loadvarData () {
    try {
        // 使用fetch API获取var.json文件内容
        const response = await fetch( './s2v.json' );
        if ( !response.ok ) {
            throw new Error( `HTTP错误! 状态码: ${ response.status }` );
        }
        // 解析JSON数据
        const varData = await response.json();
        return varData;
    } catch ( error ) {
        console.error( '加载s2v.json文件出错：', error );
        throw error; // 重新抛出错误，让调用者知道发生了错误
    }
}
class UnionFind {
    constructor () {
        this.parent = {};  // 每个字符的父节点
        this.rank = {};    // 树的高度（用于按秩合并）
    }

    // 查找根节点（路径压缩）
    find ( char ) {
        if ( this.parent[ char ] !== char ) {
            this.parent[ char ] = this.find( this.parent[ char ] );  // 路径压缩
        }
        return this.parent[ char ];
    }

    // 合并两个集合（按秩合并）
    union ( char1, char2 ) {
        const root1 = this.find( char1 );
        const root2 = this.find( char2 );

        if ( root1 === root2 ) return;

        if ( this.rank[ root1 ] > this.rank[ root2 ] ) {
            this.parent[ root2 ] = root1;
        } else if ( this.rank[ root1 ] < this.rank[ root2 ] ) {
            this.parent[ root1 ] = root2;
        } else {
            this.parent[ root2 ] = root1;
            this.rank[ root1 ]++;
        }
    }

    // 初始化字符（若未加入并查集）
    add ( char ) {
        if ( !( char in this.parent ) ) {
            this.parent[ char ] = char;
            this.rank[ char ] = 0;
        }
    }
}
function buildSimilarityIndex ( similar ) {
    const uf = new UnionFind();
    const groupMap = {};  // 集合 ID -> 所有字符

    // 遍历原始数据，建立并查集
    for ( const char in similar ) {
        uf.add( char );  // 添加当前字符
        for ( const variant of similar[ char ] ) {
            uf.add( variant );
            uf.union( char, variant );  // 合并字符与变体
        }
    }

    // 构建 groupMap
    for ( const char in uf.parent ) {
        const root = uf.find( char );
        if ( !groupMap[ root ] ) {
            groupMap[ root ] = [];
        }
        groupMap[ root ].push( char );
    }

    return {
        parentMap: uf.parent,
        groupMap
    };
}
let varObj;
function GetVariable ( char ) {
    const { parentMap, groupMap } = varObj;

    // 如果字符不在索引中，返回空数组
    if ( !( char in parentMap ) ) {
        return [];
    }

    const root = parentMap[ char ];  // 找到所属集合的根节点
    if ( !root ) {
        return [];
    }
    const group = groupMap[ root ] || [];

    // 剔除原字符，返回副本
    return group.filter( c => c !== char );
}
// 使用示例
loadvarData().then( ( varData ) => {
    // 将var数据转换为对象，方便查询
    varObj = buildSimilarityIndex( varData );
    window.varObj = varObj;
} ).catch( error => {
    console.error( '处理var.json数据时出错：', error );
} );
export { GetVariable };